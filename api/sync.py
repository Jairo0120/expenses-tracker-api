"""
Sync protocol for offline-capable clients.

Records are identified by `uuid` on the wire, and so are their references
(`cycle_uuid`, `budget_uuid`, ...); integer ids stay internal.

Pull: every change after a `sync_version` cursor, deleted records included
(with `deleted_at` set), in pages ordered by version.

Push: a list of changes applied in order, each one resolved as
- `applied`;
- `stale`: the server copy is newer, or deleted (a delete always wins);
- `merged`: the record duplicates one the server already has (a cycle for the
  same month, a saving type with the same name, a recurrent entry's copy for
  the same cycle); the client should switch to the returned record's uuid;
- `rejected`: invalid (unknown entity or reference, missing fields, ...).
The server's copy of the record comes back with every result that has one.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel as Schema, ConfigDict
from pydantic import Field as SchemaField, ValidationError
from sqlmodel import Session, select

from api.models import (
    BaseModel,
    Budget,
    Cycle,
    Expense,
    Income,
    RecurrentBudget,
    RecurrentExpense,
    RecurrentIncome,
    RecurrentSaving,
    Saving,
    SavingMovementEnum,
    SavingType,
    SourceEnum,
    SyncState,
    refresh_active_cycle,
    soft_delete,
    utcnow,
)


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


# Clients send ISO timestamps with an offset; they're stored as naive UTC.
UtcDatetime = Annotated[datetime, AfterValidator(_to_naive_utc)]


class PushData(Schema):
    """Base for the fields a client may send for an entity."""

    model_config = ConfigDict(extra="forbid")


class CycleData(PushData):
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SavingTypeData(PushData):
    description: str | None = None


class RecurrentBudgetData(PushData):
    description: str | None = None
    val_budget: float | None = None
    is_enabled: bool | None = None


class RecurrentExpenseData(PushData):
    description: str | None = None
    val_expense: float | None = None
    enabled: bool | None = None
    categories: str | None = None


class RecurrentIncomeData(PushData):
    description: str | None = None
    val_income: float | None = None
    enabled: bool | None = None


class RecurrentSavingData(PushData):
    val_saving: float | None = None
    enabled: bool | None = None
    saving_type_uuid: str | None = None


class BudgetData(PushData):
    description: str | None = None
    val_budget: float | None = None
    cycle_uuid: str | None = None
    recurrent_budget_uuid: str | None = None


class ExpenseData(PushData):
    description: str | None = None
    val_expense: float | None = None
    date_expense: UtcDatetime | None = None
    source: SourceEnum | None = None
    categories: str | None = None
    is_recurrent_expense: bool | None = None
    cycle_uuid: str | None = None
    budget_uuid: str | None = None
    recurrent_expense_uuid: str | None = None


class IncomeData(PushData):
    description: str | None = None
    val_income: float | None = None
    date_income: UtcDatetime | None = None
    is_recurrent_income: bool | None = None
    cycle_uuid: str | None = None
    recurrent_income_uuid: str | None = None


class SavingData(PushData):
    val_saving: float | None = None
    date_saving: UtcDatetime | None = None
    movement_type: SavingMovementEnum | None = None
    movement_description: str | None = None
    is_recurrent_saving: bool | None = None
    cycle_uuid: str | None = None
    saving_type_uuid: str | None = None
    recurrent_saving_uuid: str | None = None


@dataclass(frozen=True)
class Ref:
    """A reference sent as a uuid (`wire`) and stored as an id (`column`)."""

    wire: str
    column: str
    target: type[BaseModel]


@dataclass(frozen=True)
class Entity:
    name: str
    model: type[BaseModel]
    # Plain fields sent to clients (pull).
    fields: tuple[str, ...]
    refs: tuple[Ref, ...]
    # What clients may send (push), and what creating a record needs.
    push_schema: type[PushData]
    required: tuple[str, ...]
    # Owned through `user_id`, or else through its cycle.
    owned_by_user: bool
    # Limited to recent cycles when a client asks for a window.
    windowed: bool = False
    # Reference to the recurrent entry this record is a copy of.
    recurrent_ref: str | None = None
    ref_by_wire: dict[str, Ref] = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.ref_by_wire.update({ref.wire: ref for ref in self.refs})


CYCLE_REF = Ref("cycle_uuid", "cycle_id", Cycle)
SAVING_TYPE_REF = Ref("saving_type_uuid", "saving_type_id", SavingType)

# In dependency order: referenced entities first.
ENTITIES = (
    Entity(
        "cycles", Cycle,
        fields=("description", "start_date", "end_date", "is_active"),
        refs=(),
        push_schema=CycleData,
        required=("description", "start_date", "end_date"),
        owned_by_user=True,
    ),
    Entity(
        "saving_types", SavingType,
        fields=("description",),
        refs=(),
        push_schema=SavingTypeData,
        required=("description",),
        owned_by_user=True,
    ),
    Entity(
        "recurrent_budgets", RecurrentBudget,
        fields=("description", "val_budget", "is_enabled"),
        refs=(),
        push_schema=RecurrentBudgetData,
        required=("description", "val_budget"),
        owned_by_user=True,
    ),
    Entity(
        "recurrent_expenses", RecurrentExpense,
        fields=("description", "val_expense", "enabled", "categories"),
        refs=(),
        push_schema=RecurrentExpenseData,
        required=("description", "val_expense"),
        owned_by_user=True,
    ),
    Entity(
        "recurrent_incomes", RecurrentIncome,
        fields=("description", "val_income", "enabled"),
        refs=(),
        push_schema=RecurrentIncomeData,
        required=("description", "val_income"),
        owned_by_user=True,
    ),
    Entity(
        "recurrent_savings", RecurrentSaving,
        fields=("val_saving", "enabled"),
        refs=(SAVING_TYPE_REF,),
        push_schema=RecurrentSavingData,
        required=("val_saving", "saving_type_uuid"),
        owned_by_user=True,
    ),
    Entity(
        "budgets", Budget,
        fields=("description", "val_budget"),
        refs=(
            CYCLE_REF,
            Ref("recurrent_budget_uuid", "recurrent_budget_id",
                RecurrentBudget),
        ),
        push_schema=BudgetData,
        required=("description", "val_budget", "cycle_uuid"),
        owned_by_user=False,
        windowed=True,
        recurrent_ref="recurrent_budget_uuid",
    ),
    Entity(
        "expenses", Expense,
        fields=(
            "description", "val_expense", "date_expense", "source",
            "categories", "is_recurrent_expense",
        ),
        refs=(
            CYCLE_REF,
            Ref("budget_uuid", "budget_id", Budget),
            Ref("recurrent_expense_uuid", "recurrent_expense_id",
                RecurrentExpense),
        ),
        push_schema=ExpenseData,
        required=("description", "val_expense", "date_expense", "cycle_uuid"),
        owned_by_user=False,
        windowed=True,
        recurrent_ref="recurrent_expense_uuid",
    ),
    Entity(
        "incomes", Income,
        fields=("description", "val_income", "date_income",
                "is_recurrent_income"),
        refs=(
            CYCLE_REF,
            Ref("recurrent_income_uuid", "recurrent_income_id",
                RecurrentIncome),
        ),
        push_schema=IncomeData,
        required=("description", "val_income", "date_income", "cycle_uuid"),
        owned_by_user=False,
        windowed=True,
        recurrent_ref="recurrent_income_uuid",
    ),
    Entity(
        # Never windowed: savings totals add up every saving ever recorded.
        "savings", Saving,
        fields=("val_saving", "date_saving", "movement_type",
                "movement_description", "is_recurrent_saving"),
        refs=(
            CYCLE_REF,
            SAVING_TYPE_REF,
            Ref("recurrent_saving_uuid", "recurrent_saving_id",
                RecurrentSaving),
        ),
        push_schema=SavingData,
        required=("val_saving", "date_saving", "cycle_uuid",
                  "saving_type_uuid"),
        owned_by_user=False,
        recurrent_ref="recurrent_saving_uuid",
    ),
)
ENTITY_BY_NAME = {entity.name: entity for entity in ENTITIES}
ENTITY_BY_MODEL = {entity.model: entity for entity in ENTITIES}


def owned_query(entity: Entity, user_id: int):
    """All the user's records of an entity, deleted ones included."""
    model = entity.model
    statement = select(model)
    if entity.owned_by_user:
        return statement.where(model.user_id == user_id)
    return statement.join(Cycle, model.cycle_id == Cycle.id).where(
        Cycle.user_id == user_id
    )


def serialize(session: Session, records: list[BaseModel]) -> list[dict]:
    """Records as sent to clients, with references as uuids."""
    if not records:
        return []
    entity = ENTITY_BY_MODEL[type(records[0])]
    uuids_by_ref = {}
    for ref in entity.refs:
        ids = {getattr(record, ref.column) for record in records} - {None}
        uuids_by_ref[ref.wire] = dict(
            session.exec(
                select(ref.target.id, ref.target.uuid).where(
                    ref.target.id.in_(ids)
                )
            ).all()
        ) if ids else {}
    result = []
    for record in records:
        item = {
            "uuid": record.uuid,
            "sync_version": record.sync_version,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "deleted_at": record.deleted_at,
        }
        for name in entity.fields:
            item[name] = getattr(record, name)
        for ref in entity.refs:
            item[ref.wire] = uuids_by_ref[ref.wire].get(
                getattr(record, ref.column)
            )
        result.append(item)
    return result


def pull(
    session: Session,
    user_id: int,
    since: int,
    limit: int,
    window_start: date | None = None,
) -> dict[str, Any]:
    """
    The user's changes after version `since`, at most `limit`. `cursor` is
    what to pass as `since` next time; when `has_more` is false it may be past
    the last change returned (other users' changes are skipped).
    """
    # Read before the records: every version up to this one is committed
    # (writers take versions and commit one at a time).
    last_version = session.exec(select(SyncState.last_version)).first() or 0
    candidates = []
    for entity in ENTITIES:
        model = entity.model
        statement = owned_query(entity, user_id).where(
            model.sync_version > since
        )
        if window_start and entity.windowed:
            statement = statement.where(Cycle.start_date >= window_start)
        statement = statement.order_by(model.sync_version).limit(limit + 1)
        candidates += session.exec(statement).all()
    candidates.sort(key=lambda record: record.sync_version)
    page, has_more = candidates[:limit], len(candidates) > limit
    if has_more:
        cursor = page[-1].sync_version
    else:
        cursor = max([since, last_version] + [r.sync_version for r in page])
    changes = {}
    for entity in ENTITIES:
        records = [r for r in page if isinstance(r, entity.model)]
        if records:
            changes[entity.name] = serialize(session, records)
    return {"cursor": cursor, "has_more": has_more, "changes": changes}


class PushChange(Schema):
    entity: str
    uuid: UUID
    # When the client made the change (compared for "latest edit wins").
    updated_at: UtcDatetime
    deleted: bool = False
    data: dict[str, Any] = {}


class PushRequest(Schema):
    changes: list[PushChange] = SchemaField(max_length=500)


class PushResult(Schema):
    uuid: str
    status: Literal["applied", "stale", "merged", "rejected"]
    record: dict[str, Any] | None = None
    reason: str | None = None


class Rejected(Exception):
    pass


class PushProcessor:
    """Applies one push; `results` follows the order of the changes."""

    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        # Client uuid -> server uuid for records merged earlier in the push,
        # so later changes may still reference the client's uuid.
        self.aliases: dict[str, str] = {}
        self.results: list[tuple[str, str, BaseModel | None, str | None]] = []
        self.created_cycles = False

    def run(self, changes: list[PushChange]) -> list[PushResult]:
        for change in changes:
            uuid = str(change.uuid)
            try:
                status, record = self.apply(change, uuid)
                self.results.append((uuid, status, record, None))
            except Rejected as rejected:
                self.results.append((uuid, "rejected", None, str(rejected)))
            # Flush so later changes in the push see this one.
            self.session.flush()
        if self.created_cycles:
            refresh_active_cycle(
                self.session, self.user_id, utcnow().date()
            )
        self.session.commit()
        return [
            PushResult(
                uuid=uuid,
                status=status,
                record=self.serialize(record),
                reason=reason,
            )
            for uuid, status, record, reason in self.results
        ]

    def serialize(self, record: BaseModel | None):
        if record is None:
            return None
        self.session.refresh(record)
        return serialize(self.session, [record])[0]

    def apply(self, change: PushChange, uuid: str):
        entity = ENTITY_BY_NAME.get(change.entity)
        if entity is None:
            raise Rejected(f"Unknown entity {change.entity!r}")
        try:
            data = entity.push_schema.model_validate(change.data)
        except ValidationError as error:
            raise Rejected(f"Invalid data: {error.errors()[0]['msg']}")
        sent = data.model_dump(include=data.model_fields_set)

        record = self.session.exec(
            select(entity.model).where(entity.model.uuid == uuid)
        ).first()
        if record is not None and not self.owns(entity, record):
            raise Rejected("Unknown record")

        if record is not None:
            if record.deleted_at is not None:
                # A delete always wins; a second delete is a no-op.
                return ("applied" if change.deleted else "stale"), record
            if change.deleted:
                soft_delete(self.session, record)
                record.updated_at = change.updated_at
                return "applied", record
            if change.updated_at < record.updated_at:
                return "stale", record
            self.assign(entity, record, sent)
            record.updated_at = change.updated_at
            self.session.add(record)
            return "applied", record

        if change.deleted:
            # Created and deleted while offline: nothing to keep.
            return "applied", None
        missing = [name for name in entity.required if sent.get(name) is None]
        if missing:
            raise Rejected(f"Missing {', '.join(missing)}")
        values = self.resolve(entity, sent)

        duplicate = self.find_duplicate(entity, values)
        if duplicate is not None:
            self.aliases[uuid] = duplicate.uuid
            if duplicate.deleted_at is not None:
                return "stale", duplicate
            return "merged", duplicate

        record = entity.model(
            uuid=uuid,
            created_at=change.updated_at,
            updated_at=change.updated_at,
            **values,
        )
        if entity.owned_by_user:
            record.user_id = self.user_id
        self.check_budget_cycle(record)
        self.session.add(record)
        if entity.model is Cycle:
            self.created_cycles = True
        return "applied", record

    def assign(self, entity: Entity, record: BaseModel, sent: dict):
        for name, value in self.resolve(entity, sent).items():
            setattr(record, name, value)
        if entity.model is Expense and record.budget_id is not None:
            self.check_budget_cycle(record)

    def resolve(self, entity: Entity, sent: dict) -> dict:
        """Sent values as model attributes, references turned into ids."""
        values = {}
        for name, value in sent.items():
            ref = entity.ref_by_wire.get(name)
            if ref is None:
                if entity.model is SavingType and name == "description":
                    # Saving types are named like the create endpoint does.
                    value = value.capitalize()
                values[name] = value
            else:
                values[ref.column] = self.resolve_ref(ref, value)
        if entity.model is Cycle:
            start = values.get("start_date")
            end = values.get("end_date")
            if start and end and start > end:
                raise Rejected("start_date is after end_date")
        return values

    def resolve_ref(self, ref: Ref, uuid: str | None) -> int | None:
        if uuid is None:
            return None
        uuid = self.aliases.get(uuid, uuid)
        target = self.session.exec(
            select(ref.target)
            .where(ref.target.uuid == uuid)
            .where(ref.target.deleted_at.is_(None))
        ).first()
        target_entity = ENTITY_BY_MODEL[ref.target]
        if target is None or not self.owns(target_entity, target):
            raise Rejected(f"Unknown {ref.wire} {uuid}")
        return target.id

    def owns(self, entity: Entity, record: BaseModel) -> bool:
        if entity.owned_by_user:
            return record.user_id == self.user_id
        cycle = self.session.get(Cycle, record.cycle_id)
        return cycle is not None and cycle.user_id == self.user_id

    def check_budget_cycle(self, record: BaseModel):
        if isinstance(record, Expense) and record.budget_id is not None:
            budget = self.session.get(Budget, record.budget_id)
            if budget.cycle_id != record.cycle_id:
                raise Rejected("The budget belongs to another cycle")

    def find_duplicate(self, entity: Entity, values: dict):
        """The existing record a new one duplicates, deleted ones included."""
        model = entity.model
        statement = None
        if model is Cycle:
            statement = (
                select(Cycle)
                .where(Cycle.user_id == self.user_id)
                .where(Cycle.start_date == values["start_date"])
            )
        elif model is SavingType:
            statement = (
                select(SavingType)
                .where(SavingType.user_id == self.user_id)
                .where(SavingType.description == values["description"])
                .where(SavingType.deleted_at.is_(None))
            )
        elif entity.recurrent_ref:
            column = entity.ref_by_wire[entity.recurrent_ref].column
            if values.get(column) is not None:
                statement = (
                    select(model)
                    .where(model.cycle_id == values["cycle_id"])
                    .where(getattr(model, column) == values[column])
                )
        if statement is None:
            return None
        return self.session.exec(statement).first()
