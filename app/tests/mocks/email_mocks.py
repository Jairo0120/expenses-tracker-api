BAD_EMAIL = '''
    Received: from XXXXXXXXXX.namprd06.prod.outlook.com
    (1803:20b8:312:1-9::9)by XXXXXXXXXX.namprd06.prod.outlook.com
    with HTTPS; Thu, 23 Feb 202301:14:04 +0000\r\nReceived: from
    XXXXXXXXXXXX.namprd14.prod.outlook.com (1111:22222:5:19l::19)
    n d=***REMOVED***;h=From:To:Subject:Date:List
    : 0\r\nX-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aa
    lEKzlldkEwenlQM0Ru?==?utf-8?B?ZXhJekpFSnBWRVdReG1odURVREZ3NVpY
    .lifemiles.com/?qs=0a659d55eb3bdc9c25e0767f9e8b3026e1e234a6882f94f81bd2e
    body/eight: auto !important;margin-left: auto !i
    html>; }.mobile-hidden { display:n !important; }logo { d
    </html>
    '''

MISSING_HTML_BODY_EMAIL = '''
    Received: from XXXXXXXXXX.namprd06.prod.outlook.com
    (1803:20b8:312:1-9::9)by XXXXXXXXXX.namprd06.prod.outlook.com
    with HTTPS; Thu, 23 Feb 202301:14:04 +0000\r\nReceived: from
    XXXXXXXXXXXX.namprd14.prod.outlook.com (1111:22222:5:19l::19)
    n d=***REMOVED***;h=From:To:Subject:Date:List
    : 0\r\nX-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aa
    lEKzlldkEwenlQM0Ru?==?utf-8?B?ZXhJekpFSnBWRVdReG1odURVREZ3NVpY
    .lifemiles.com/?qs=0a659d55eb3bdc9c25e0767f9e8b3026e1e234a6882f94f81bd2e
    body/eight: auto !important;margin-left: auto !i
    html>; }.mobile-hidden { display:n !important; }logo { d
    </html>
    <html>
    some text
    </body>
    </html>
'''

GOOD_EMPTY_EMAIL = '''
    Received: from XXXXXXXXXX.namprd06.prod.outlook.com
    (1803:20b8:312:1-9::9)by XXXXXXXXXX.namprd06.prod.outlook.com
    with HTTPS; Thu, 23 Feb 202301:14:04 +0000\r\nReceived: from
    XXXXXXXXXXXX.namprd14.prod.outlook.com (1111:22222:5:19l::19)
    n d=***REMOVED***;h=From:To:Subject:Date:List
    : 0\r\nX-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aa
    lEKzlldkEwenlQM0Ru?==?utf-8?B?ZXhJekpFSnBWRVdReG1odURVREZ3NVpY
    .lifemiles.com/?qs=0a659d55eb3bdc9c25e0767f9e8b3026e1e234a6882f94f81bd2e
    body/eight: auto !important;margin-left: auto !i
    html>; }.mobile-hidden { display:n !important; }logo { d
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
    <html><head>\r\n
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
    maximum-scale=1, user-scalable=0">\r\n
    <style type="text/css">ReadMsgBody{ width: 100%;}\r\n
    .ExternalClass {width: 100%;}.ExternalClass, .ExternalClass p,
    .ExternalClass span, .ExternalClass
    font, .ExternalClass td, .ExternalClass div {line-height: 100%;}\r\n
    body {-webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;
    margin:0 !important;}</style>
    </head>
    <body bgcolor="#ffffff" style="background-color: #ffffff;
    color: #000000; padding: 0px; -webkit-text-size-adjust:none;
    font-size: 16px; font-family:arial,helvetica,sans-serif;" text="#000000">
    </body></html>
    '''

INCOMPLETE_HTML_EMAIL = '''
    Received: from XXXXXXXXXX.namprd06.prod.outlook.com
    (1803:20b8:312:1-9::9)by XXXXXXXXXX.namprd06.prod.outlook.com
    with HTTPS; Thu, 23 Feb 202301:14:04 +0000\r\nReceived: from
    XXXXXXXXXXXX.namprd14.prod.outlook.com (1111:22222:5:19l::19)
    n d=***REMOVED***;h=From:To:Subject:Date:List
    : 0\r\nX-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aa
    lEKzlldkEwenlQM0Ru?==?utf-8?B?ZXhJekpFSnBWRVdReG1odURVREZ3NVpY
    .lifemiles.com/?qs=0a659d55eb3bdc9c25e0767f9e8b3026e1e234a6882f94f81bd2e
    body/eight: auto !important;margin-left: auto !i
    html>; }.mobile-hidden { display:n !important; }logo { d
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
    <html><head>\r\n
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
    maximum-scale=1, user-scalable=0">\r\n
    <style type="text/css">ReadMsgBody{ width: 100%;}\r\n
    .ExternalClass {width: 100%;}.ExternalClass, .ExternalClass p,
    .ExternalClass span, .ExternalClass
    font, .ExternalClass td, .ExternalClass div {line-height: 100%;}\r\n
    body {-webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;
    margin:0 !important;}>
    </head>
    <body bgcolor="#ffffff" text="#000000" style="background-color: #ffffff;
    color: #000000; padding: 0px; -webkit-text-size-adjust:none;
    font-size: 16px; font-family:arial,helvetica,sans-serif;">
    <h1>Some header</h1>
    <div class="some-class" id="some-id">Some random content</div>
    <section>Some text for this section</section>
    <table><thead><th>Some column</th></thead><tbody><tr><td>Some content</td>
    </tr></tbody></table>
    <footer>
    Some footer
    </footer>
    </body>
    </html>
    '''

GOOD_FULL_EMAIL = '''
    Received: from XXXXXXXXXX.namprd06.prod.outlook.com
    (1803:20b8:312:1-9::9)by XXXXXXXXXX.namprd06.prod.outlook.com
    with HTTPS; Thu, 23 Feb 202301:14:04 +0000\r\nReceived: from
    XXXXXXXXXXXX.namprd14.prod.outlook.com (1111:22222:5:19l::19)
    n d=***REMOVED***;h=From:To:Subject:Date:List
    : 0\r\nX-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aa
    lEKzlldkEwenlQM0Ru?==?utf-8?B?ZXhJekpFSnBWRVdReG1odURVREZ3NVpY
    .lifemiles.com/?qs=0a659d55eb3bdc9c25e0767f9e8b3026e1e234a6882f94f81bd2e
    body/eight: auto !important;margin-left: auto !i
    html>; }.mobile-hidden { display:n !important; }logo { d
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
    "http://www.w3.org/TR/html4/loose.dtd">
    <html><head>\r\n
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1,
    maximum-scale=1, user-scalable=0">\r\n
    <style type="text/css">ReadMsgBody{ width: 100%;}\r\n
    .ExternalClass {width: 100%;}.ExternalClass, .ExternalClass p,
    .ExternalClass span, .ExternalClass
    font, .ExternalClass td, .ExternalClass div {line-height: 100%;}\r\n
    body {-webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;
    margin:0 !important;}</style>
    </head>
    <body>
    <h1>Some header</h1>
    <div class="some-class" id="some-id">Some random content</div>
    <section>Some text for this section</section>
    <table><thead><th>Some column</th></thead><tbody><tr><td>Some content</td>
    </tr></tbody></table>
    <footer>
    Some footer
    </footer>
    </body>
    </html>
    '''

ITAU_BAD_TABLE_STRUCTURE = '''
    nContent-Type: text/html; charset=us-asciiContent-Transfer-Encoding:
    7bit<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=us-ascii">
    </head>

    <body>Estimado Sr(a). John Doe: <br><table><tr><td>
    Se realiz&oacute;
    una compra en DIDI FOOD*DL desde tu Tarjeta
    Credito n&uacute;mero *****7651 de Ita&uacute;: </td>
    </tr></table> <br><table><tr>
    <td>$29,300</td></tr><tr><td>Fecha y hora: </td><td>2023/02/14
    18:25:12</td></tr></table> <br><br>Cualquier inquietud,
    comun&iacute;cate con
    nuestro N&uacute;mero &Uacute;nico por ciudad:<table width="660px"><tr><td>
    Bogot&aacute; </td><td>581 8181</td><td>C/gena </td><td>693 1818
    </td><td>Medell&iacute;n </td><td> 604 1818</td><td>Cali </td>
    <td> 486 1818</td></tr><tr><td>B/manga </td><td> 697
        1818 </td><td>Pereira </td><td> 340 1818</td><td>B/quilla </td>
    <td> 385 1818</td><td>Manizales </td><td> 887 9818</td></tr>
    </table><table width="660px"><tr align="center"><td>Otras ciudades 018000
            512633</td></tr></table> <br><small>Este mensaje ha sido enviado
    autom&aacute;ticamente, por favor no respondas
    a esta direcci&oacute;n de correo
    electr&oacute;nico.</small></body>
    '''

ITAU_GOOD_TABLE_STRUCTURE = '''
    nContent-Type: text/html; charset=us-asciiContent-Transfer-Encoding:
    7bit<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=us-ascii">
    </head>

    <body>Estimado Sr(a). John Doe: <br><table><tr><td>
    Se realiz&oacute;
    una compra en DIDI FOOD*DL desde tu Tarjeta
    Credito n&uacute;mero *****7651 de Ita&uacute;: </td>
    </tr></table> <br><table><tr><td>Monto: </td>
    <td>$29,300.21</td></tr><tr><td>Fecha y hora: </td><td>2023/02/14
    18:25:12</td></tr></table> <br><br>Cualquier inquietud,
    comun&iacute;cate con
    nuestro N&uacute;mero &Uacute;nico por ciudad:<table width="660px"><tr><td>
    Bogot&aacute; </td><td>581 8181</td><td>C/gena </td><td>693 1818
    </td><td>Medell&iacute;n </td><td> 604 1818</td><td>Cali </td>
    <td> 486 1818</td></tr><tr><td>B/manga </td><td> 697
        1818 </td><td>Pereira </td><td> 340 1818</td><td>B/quilla </td>
    <td> 385 1818</td><td>Manizales </td><td> 887 9818</td></tr>
    </table><table width="660px"><tr align="center"><td>Otras ciudades 018000
            512633</td></tr></table> <br><small>Este mensaje ha sido enviado
    autom&aacute;ticamente, por favor no respondas
    a esta direcci&oacute;n de correo
    electr&oacute;nico.</small></body>
    '''

ITAU_BAD_EXPENSE_VALUE = '''
    nContent-Type: text/html; charset=us-asciiContent-Transfer-Encoding:
    7bit<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=us-ascii">
    </head>

    <body>Estimado Sr(a). John Doe: <br><table><tr><td>
    Se realiz&oacute;
    una compra en DIDI FOOD*DL desde tu Tarjeta
    Credito n&uacute;mero *****7651 de Ita&uacute;: </td>
    </tr></table> <br><table><tr><td>Monto: </td>
    <td>$29.300.21</td></tr><tr><td>Fecha y hora: </td><td>2023/02/14
    18:25:12</td></tr></table> <br><br>Cualquier inquietud,
    comun&iacute;cate con
    nuestro N&uacute;mero &Uacute;nico por ciudad:<table width="660px"><tr><td>
    Bogot&aacute; </td><td>581 8181</td><td>C/gena </td><td>693 1818
    </td><td>Medell&iacute;n </td><td> 604 1818</td><td>Cali </td>
    <td> 486 1818</td></tr><tr><td>B/manga </td><td> 697
        1818 </td><td>Pereira </td><td> 340 1818</td><td>B/quilla </td>
    <td> 385 1818</td><td>Manizales </td><td> 887 9818</td></tr>
    </table><table width="660px"><tr align="center"><td>Otras ciudades 018000
            512633</td></tr></table> <br><small>Este mensaje ha sido enviado
    autom&aacute;ticamente, por favor no respondas
    a esta direcci&oacute;n de correo
    electr&oacute;nico.</small></body>
    '''

ITAU_BAD_DATE_VALUE = '''
    nContent-Type: text/html; charset=us-asciiContent-Transfer-Encoding:
    7bit<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=us-ascii">
    </head>

    <body>Estimado Sr(a). John Doe: <br><table><tr><td>
    Se realiz&oacute;
    una compra en DIDI FOOD*DL desde tu Tarjeta
    Credito n&uacute;mero *****7651 de Ita&uacute;: </td>
    </tr></table> <br><table><tr><td>Monto: </td>
    <td>29300.21</td></tr><tr><td>Fecha y hora: </td><td>20202/14
    18:25:12</td></tr></table> <br><br>Cualquier inquietud,
    comun&iacute;cate con
    nuestro N&uacute;mero &Uacute;nico por ciudad:<table width="660px"><tr><td>
    Bogot&aacute; </td><td>581 8181</td><td>C/gena </td><td>693 1818
    </td><td>Medell&iacute;n </td><td> 604 1818</td><td>Cali </td>
    <td> 486 1818</td></tr><tr><td>B/manga </td><td> 697
        1818 </td><td>Pereira </td><td> 340 1818</td><td>B/quilla </td>
    <td> 385 1818</td><td>Manizales </td><td> 887 9818</td></tr>
    </table><table width="660px"><tr align="center"><td>Otras ciudades 018000
            512633</td></tr></table> <br><small>Este mensaje ha sido enviado
    autom&aacute;ticamente, por favor no respondas
    a esta direcci&oacute;n de correo
    electr&oacute;nico.</small></body>
    '''

BANCOLOMBIA_PSE_GOOD = '''
    <table class="mce-item-table"
        data-mce-style="width: 531.54px; margin-left: auto;
        margin-right: auto;" style="width: 531.54px; margin-left: auto;
        margin-right: auto;">
        <tbody>
            <tr data-mce-style="height: 29px;" style="height: 29px;">
                <td data-mce-style="text-align: center; width: 526.54px;
                height: 29px;" style="text-align: center; width: 526.54px;
                height: 29px;">
                <span data-mce-style="font-family: helvetica, arial,
                sans-serif; font-size: 14pt; color: #3366ff;"
                        style="font-family: helvetica, arial, sans-serif;
                        font-size: 18pt; color: #105ea8;font-weight: bold;">
                        ¡Hola, John Doe</span></td>
            </tr>
            <tr data-mce-style="height: 190.173px;" style="height: 190.173px;">
                <td data-mce-style="width: 526.54px; height: 190.173px;"
                    style="width: 526.54px; height: 190.173px;"><br /><b
                        data-mce-style="color: #0059a4; font-family: Roboto,
                        sans-serif; font-size: 16px; text-align: center;"
                        style="color: #0059a4; font-family: Roboto,
                        sans-serif; font-size: 16px; text-align: center;"><span
                            color="#0059a4" face="Roboto, sans-serif"><b><span
                                    data-mce-style="font-family: helvetica,
                                    arial, sans-serif;"
                                    style="font-family: helvetica, arial,
                                    sans-serif;"><span
                                        data-mce-style="color: #999999;
                                        font-size: 14pt;"
                                        style="color: #999999;
                                        font-size: 14pt;">Gracias por
                                        utilizar los servicios de
                                        BANCOLOMBIA\xa0</span><span
                                        data-mce-style="color: #999999;
                                        font-size: 14pt;"
                                        style="color: #999999;
                                        font-size: 14pt;">y
                                        PSE. los siguientes son los datos de tu
                                        transacción:</span></span></b></span>
                                        </b><br /><br /><span
                        data-mce-style="font-size: 12pt;
                        font-family: helvetica, arial, sans-serif;"
                        style="font-size: 12pt; font-family: helvetica, arial,
                        sans-serif;"><span
                            color="#0059a4" face="Roboto, sans-serif"><span
                                data-mce-style="color: #999999;"
                                style="color: #999999;">Estado de
                                la Transacción: Aprobada</span></span><br />
                                <span color="#0059a4"
                            face="Roboto, sans-serif">
                            <span data-mce-style="color: #999999;"
                                style="color: #999999;">CUS: 1975974114</span>
                                <br /><span
                                data-mce-style="color: #999999;"
                                style="color: #999999;">Empresa:
                                CONSORCIO EMCALI</span><br />
                                <span data-mce-style="color: #999999;"
                                style="color: #999999;">Descripción:\xa0</span>
                                </span><span
                            data-mce-style="color: #999999;"
                            style="color: #999999;">Factura
                            Servicios Publicos<br />Valor de la
                            Transacción: $ 257.455<br />Fecha de
                            Transacción: 17/03/2023</span></span></td>
            </tr>
        </tbody>
    </table>
'''

BANCOLOMBIA_PSE_INCOMPLETE_DATA = '''
    <table class="mce-item-table"
        data-mce-style="width: 531.54px; margin-left: auto;
        margin-right: auto;" style="width: 531.54px; margin-left: auto;
        margin-right: auto;">
        <tbody>
            <tr data-mce-style="height: 29px;" style="height: 29px;">
                <td data-mce-style="text-align: center; width: 526.54px;
                height: 29px;" style="text-align: center; width: 526.54px;
                height: 29px;">
                <span data-mce-style="font-family: helvetica, arial,
                sans-serif; font-size: 14pt; color: #3366ff;"
                        style="font-family: helvetica, arial, sans-serif;
                        font-size: 18pt; color: #105ea8;font-weight: bold;">
                        ¡Hola, John Doe</span></td>
            </tr>
            <tr data-mce-style="height: 190.173px;" style="height: 190.173px;">
                <td data-mce-style="width: 526.54px; height: 190.173px;"
                    style="width: 526.54px; height: 190.173px;"><br /><b
                        data-mce-style="color: #0059a4; font-family: Roboto,
                        sans-serif; font-size: 16px; text-align: center;"
                        style="color: #0059a4; font-family: Roboto,
                        sans-serif; font-size: 16px; text-align: center;"><span
                            color="#0059a4" face="Roboto, sans-serif"><b><span
                                    data-mce-style="font-family: helvetica,
                                    arial, sans-serif;"
                                    style="font-family: helvetica, arial,
                                    sans-serif;"><span
                                        data-mce-style="color: #999999;
                                        font-size: 14pt;"
                                        style="color: #999999;
                                        font-size: 14pt;">Gracias por
                                        utilizar los servicios de
                                        BANCOLOMBIA\xa0</span><span
                                        data-mce-style="color: #999999;
                                        font-size: 14pt;"
                                        style="color: #999999;
                                        font-size: 14pt;">y
                                        PSE. los siguientes son los datos de tu
                                        transacción:</span></span></b></span>
                                        </b><br /><br /><span
                        data-mce-style="font-size: 12pt;
                        font-family: helvetica, arial, sans-serif;"
                        style="font-size: 12pt; font-family: helvetica, arial,
                        sans-serif;"><span
                            color="#0059a4" face="Roboto, sans-serif"><span
                                data-mce-style="color: #999999;"
                                style="color: #999999;">Estado de
                                la Transacción: Aprobada</span></span><br />
                                <span color="#0059a4"
                            face="Roboto, sans-serif">
                            <span data-mce-style="color: #999999;"
                                style="color: #999999;">CUS: 1975974114</span>
                                <br /><span
                                data-mce-style="color: #999999;"
                                style="color: #999999;">Empresa:
                                CONSORCIO EMCALI</span><br />
                                <span data-mce-style="color: #999999;"
                                style="color: #999999;">Descripción:\xa0</span>
                                </span><span
                            data-mce-style="color: #999999;"
                            style="color: #999999;">Factura
                            Servicios Publicos<br />Fecha de
                            Transacción: 17/03/2023</span></span></td>
            </tr>
        </tbody>
    </table>
'''

BANCOLOMBIA_PSE_REJECTED = '''
    <table class="mce-item-table" data-mce-style="width: 700px;
    margin-left: auto; margin-right: auto;"
    style="width: 700px; margin-left: auto; margin-right: auto;">\n<tbody>\n<tr
    data-mce-style="height: 340.088px;" style="height: 340.088px;">\n<td
    data-mce-style="width: 10.7244px; height: 340.088px;"
    style="width: 10.7244px; height: 340.088px;">\n<img alt="" data-mce-=""
    data-mce-style="display: block; margin-left: auto; margin-right: auto;"
    height="341"
    src="https://www.psepagos.co/images_ticketoffice/email/img1.jpg"
    style="display: block; margin-left: auto;\n margin-right: auto;"
    width="700" /></td>\n</tr>\n<tr data-mce-style="height: 235px;"
    style="height: 235px;">\n<td
    data-mce-style="width: 10.7244px; height: 235px;" style="width: 10.7244px;
    height: 235px;">\n
    <table class="mce-item-table"
    data-mce-style="width: 531.54px; margin-left: auto; margin-right: auto;"
    style="width: 531.54px; margin-left: auto; margin-right: auto;">\n<tbody>
    <tr data-mce-style="height: 29px;" style="height: 29px;">\n<td
    data-mce-style="text-align: center; width: 526.54px; height: 29px;"
    style="text-align: center; width: 526.54px; height: 29px;">\n<span
    data-mce-style="font-family: helvetica, arial, sans-serif; font-size: 14pt;
    color: #3366ff;"
    style="font-family: helvetica, arial, sans-serif; font-size: 18pt;
    color: #105ea8;\n font-weight: bold;">¡Hola,
    John Doe</span></td>\n</tr>\n<tr
    data-mce-style="height: 190.173px;" style="height: 190.173px;">\n<td
    data-mce-style="width: 526.54px; height: 190.173px;"
    style="width: 526.54px; height: 190.173px;">\n<br />\n<b
    data-mce-style="color: #0059a4; font-family: Roboto, sans-serif;
    font-size: 16px; text-align: center;"
    style="color: #0059a4; font-family: Roboto, sans-serif; font-size: 16px;
    text-align: center;"><span
    color="#0059a4" face="Roboto, sans-serif"><b><span
    data-mce-style="font-family: helvetica, arial, sans-serif;"
    style="font-family: helvetica, arial, sans-serif;"><span
    data-mce-style="color: #999999; font-size: 14pt;"
    style="color: #999999; font-size: 14pt;">Gracias por
    utilizar los servicios de BANCOLOMBIA\xa0</span><span
    data-mce-style="color: #999999; font-size: 14pt;"
    style="color: #999999;\n font-size: 14pt;">y
    PSE. los siguientes son los datos de tu
    transacción:</span></span></b></span></b><br />\n<br />\n<span
    data-mce-style="font-size: 12pt; font-family: helvetica, arial,
    sans-serif;"
    style="font-size: 12pt; font-family: helvetica, arial, sans-serif;"><span
    color="#0059a4" face="Roboto, sans-serif"><span
    data-mce-style="color: #999999;" style="color: #999999;">Estado de
    la Transacción: Rechazada</span></span><br />\n<span color="#0059a4"
    face="Roboto, sans-serif"><span data-mce-style="color: #999999;"
    style="color: #999999;">CUS: 2110147747</span><br />\n<span
    data-mce-style="color: #999999;" style="color: #999999;">Empresa:
    BANCO DE CREDITO DECOLOMBIA</span><br />\n<span
    data-mce-style="color: #999999;"
    style="color: #999999;">Descripción:\xa0</span></span><span
    data-mce-style="color: #999999;" style="color: #999999;">Otro
    valor<br />\n\t\t\t\t\t\t\t\t\t\t\tValor de la Transacción: $
    223.608<br />\n\t\t\t\t\t\t\t\t\t\t\tFecha de Transacción:
    31/05/2023</span></span></td>\n</tr>\n</tbody>\n</table>
'''
