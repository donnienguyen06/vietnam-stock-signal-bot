var sDomain = "/du-lieu/";
var currentTime = parseFloat("141251");

// Preserve the page's existing jQuery/$ in case other scripts load another jQuery later.
// This helps prevent plugins like $.fn.autocomplete / $.fn.slimScroll from becoming undefined.
var __CafeF_PageJQ = window.jQuery;
var __CafeF_Page$ = window.$;
window.addEventListener(
    "load",
    function () {
        try {
            if (
                __CafeF_PageJQ &&
                window.jQuery &&
                __CafeF_PageJQ !== window.jQuery &&
                typeof window.jQuery.noConflict === "function"
            ) {
                // Detach the newer jQuery from global namespace and restore the original one.
                window.jQuery.noConflict(true);
                window.jQuery = __CafeF_PageJQ;
                window.$ = __CafeF_Page$;
            }
        } catch (e) { }
    },
    false
);

function loadBoxChungKhoan() {
    $("#macktheodoi").length > 0 &&
        ($("#macktheodoi").attr("delay")
            ? CafeF_StockSymbol.init("macktheodoi", !0)
            : CafeF_StockSymbol.init("macktheodoi", !1));
}

function slimScrollBoxTinMois() {
    $.ajax({
        dataType: "json",
        url: "https://cafef.vn/api/getListNewestTop.chn",
        success: function (t) {
            for (var e = "", i = 0; i < t.length; i++) {
                var o = t[i],
                    s = new Date(o.PublishedDate * 1000);
                e +=
                    "<li data-id='" +
                    o.NewsId +
                    "'><span class='time'>" +
                    _formatTime(s.getHours()) +
                    ":" +
                    _formatTime(s.getMinutes()) +
                    "</span><span class='border_split'></span><a href=\"//cafef.vn" +
                    o.Url +
                    "\"><span class='inner'>" +
                    o.Title +
                    "</span></a></li>";
            }
            $("#listNewHeaderNew ul").html(e);
        },
    });
    try {
        if ($ && $.fn && ($.fn.slimScroll || $.fn.slimscroll)) {
            var fn = $.fn.slimScroll ? "slimScroll" : "slimscroll";
            $("#listNewHeaderNew")[fn]({
                height: 155,
                color: "#c6c6c6",
                size: "18px",
                opacity: 0.7,
                alwaysVisible: !0,
                railVisible: !0,
                railColor: "#dbdfe5",
                allowPageScroll: !1,
            });
        }
    } catch (e) { }
    $("#listNewHeaderNew li").each(function () {
        var t = $(this),
            e = t.height() - 8;
        t.find(".border_split").css("height", e);
    });
}

function GetCompanyInfoLink(t) {
    if ("VNINDEX" == t)
        return (
            sDomain + "/Lich-su-giao-dich-Symbol-VNINDEX/Trang-1-0-tab-1.chn"
        );
    if ("HNX-INDEX" == t)
        return (
            sDomain + "/Lich-su-giao-dich-Symbol-HNX-INDEX/Trang-1-0-tab-1.chn"
        );
    if ("UPCOM-INDEX" == t)
        return (
            sDomain +
            "/Lich-su-giao-dich-Symbol-UPCOM-INDEX/Trang-1-0-tab-1.chn"
        );
    var e = "#";
    if ("undefined" != typeof oc)
        for (i = 0; i < oc.length; i++)
            if (oc[i].c?.toLowerCase() == t?.toLowerCase()) {
                var o = "hose";
                "2" == oc[i].san && (o = "hastc"),
                    "8" == oc[i].san && (o = "otc"),
                    "9" == oc[i].san && (o = "upcom");
                var s = oc[i].m;
                s.lastIndexOf("(") > 0 &&
                    (s = s.substring(0, s.lastIndexOf("("))),
                    (s = UnicodeToKoDauAndGach($.trim(s))),
                    (e = sDomain + "/" + o + "/" + t + "-" + s + ".chn");
                break;
            }
    return e;
}

function GetCompanyName(t) {
    var e = "";
    if ("undefined" != typeof oc)
        for (var i = 0; i < oc.length; i++)
            if (oc[i].c?.toLowerCase() == t?.toLowerCase()) {
                var o = oc[i].m;
                o.lastIndexOf("(") > 0 &&
                    (o = o.substring(0, o.lastIndexOf("("))),
                    (e = o);
                break;
            }
    return e;
}

function CafeF_FormatNumber(t, e, o, s) {
    for (
        var l = (t = t.toFixed(e)).toString(), a = l.substr(l.length - e, e);
        "" != a && "0" == a.charAt(a.length - 1);

    )
        a = a.substr(0, a.length - 1);
    "" != a && (a = o + a);
    var n = l.substr(0, l.length - 3);
    if ("" != s && n.length > 3) {
        for (h = n, n = "", j = 3; j < h.length; j += 3)
            (i = h.slice(h.length - j, h.length - j + 3)), (n = s + i + n + "");
        (j = h.substr(0, h.length % 3 == 0 ? 3 : h.length % 3)), (n = j + n);
    }
    return (l = n + a);
}

function _formatTime(t) {
    return parseInt(t) < 10 ? "0" + t : t;
}

var CafeF_StockSymbol = {
    sigNalRConfig: {
        hub: {
            priceHub: 'priceshub',
        },
        action: {
            joinChannel: 'JoinChannel',
            leaveChannel: 'LeaveChannel',
            RealtimePrice: 'RealtimePrice'
        },
        type: {
            invoke: 'invoke',
            on: 'on'
        }
    },
    curentData: {},
    sigNalR: null,
    bm_st_time_exp: 262800,
    bm_st_state_time_exp: 720,
    CookiesName: "favorite_stocks",
    StateCookiesName: "favorite_stocks_state",
    AUTO_REFRESH_TIME: 15e3,
    timerId_Refresh: -1,
    IsLogged: 0,
    MaxSymbolsInQueue: 100,
    MaxSymbolsDisplay: 100,
    OldCellDatas: [],
    image_folder: "http://cafef.mediacdn.vn/frontend/images",
    script_object: null,
    stock_symbols_data: null,
    symbol_list: "",
    display_list: "",
    staticData: [],
    instance_name: "CafeF_StockSymbol",
    containerId: "",
    StockTrading_StartTime: "09:00:00",
    StockTrading_EndTime: "15:02:00",
    StockTrading_DayOfWeek: "1,2,3,4,5",
    Fields: {
        Price: 0,
        Change: 1,
        ChangePercent: 2,
        ceiling: 3,
        floor: 4,
    },
    TabTinMoi: "0",
    LastUpdateTinMoi: "",
    init: function (t, e) {
        var i = this;
        !(function () {
            for (var o = 0; o < i.MaxSymbolsDisplay; o++)
                i.OldCellDatas[o] = "";
            null != t && "" != t &&
                ((i.containerId = t), i.InitSlideTemplate(t));
            i.LoadSymbolData(!0)
        })();

        // get data realtime
        i.SignalRInit();
    },
    CreateCssLink: function (t) {
        var e = document.createElement("link");
        (e.type = "text/css"),
            (e.rel = "stylesheet"),
            (e.href = t),
            document.getElementsByTagName("head")[0].appendChild(e);
    },
    IsStockTrading: function () {
        var t = new Date(),
            e = new Date(),
            i = new Date(),
            o = this,
            s = "," + o.StockTrading_DayOfWeek + ",",
            l = o.StockTrading_StartTime.split(":"),
            a = o.StockTrading_EndTime.split(":");
        return (
            t.setHours(l[0], l[1], l[2]),
            e.setHours(a[0], a[1], a[2]),
            i >= t && i <= e && s.indexOf("," + i.getDay() + ",") >= 0
        );
    },
    InitSlideTemplate: function (t) {
        var e = !1,
            i = this;
        (window.location.pathname.indexOf("doc-nhanh.") > 0 ||
            window.location.pathname.indexOf("doc-nhanh/") > 0) &&
            (e = !0);
        try { i.MigrateFavoriteStocksCookie(); } catch (ex) { }
        var o = 0;
        e &&
            (document.location.toString().indexOf("/1/") > 0
                ? (o = 1)
                : document.location.toString().indexOf("/doc-nhanh.chn") >= 0
                    ? (o = 1)
                    : document.location.toString().indexOf("/2/") > 0 && (o = 2)),
            (i.TabTinMoi = o);
        var s = new Date();
        i.LastUpdateTinMoi =
            s.getFullYear() +
            "/" +
            (s.getMonth() + 1) +
            "/" +
            ("00" + s.getDate()).substr(("00" + s.getDate()).length - 2, 2) +
            " " +
            ("00" + s.getHours()).substr(("00" + s.getHours()).length - 2, 2) +
            ":" +
            ("00" + s.getMinutes()).substr(
                ("00" + s.getMinutes()).length - 2,
                2
            ) +
            ":" +
            ("00" + s.getSeconds()).substr(
                ("00" + s.getSeconds()).length - 2,
                2
            );
        var l = "";
        (l += "<ul>"),
            (l +=
                '<li class="wait only1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait only1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait only1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait only1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait only1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait only1024 end1024" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l +=
                '<li class="wait end" title="Click vào đây để chọn mã chứng khoán cần theo dõi" >Chọn mã CK<br />cần theo dõi</li>'),
            (l += "</ul>"),
            (l +=
                '<a href="javascript:void(0);" class="icon_dropdown sprite"><i class="inner"></i></a>'),
            jQuery("#" + t).html(l),
            jQuery("#" + t)
                .find(".icon_dropdown")
                .unbind("click")
                .bind("click", function () {
                    $(this).hasClass("active") ? i.ClosePopup() : i.OpenPopup();
                }),
            jQuery("#" + t)
                .find("li.wait")
                .unbind("click")
                .bind("click", function () {
                    i.OpenPopup();
                }),
            jQuery("#" + t)
                .find(".seting")
                .unbind("click")
                .bind("click", function () {
                    i.OpenPopup();
                }),
            jQuery("#" + t)
                .find(".prev")
                .unbind("click")
                .bind("click", function () {
                    i.MoveLeft();
                }),
            jQuery("#" + t)
                .find(".next")
                .unbind("click")
                .bind("click", function () {
                    i.MoveRight();
                }),
            (l =
                '<div class="clearmck"><div id="CafeF_StockSymbolSlidePopup" class="add-stock-popup">'),
            (l += '<div class="popup-row">'),
            (l +=
                '<div class="in-placeholder"><input type="text" id="CafeF_StockSymbolSlideKeyword" placeholder="Mã chứng khoán muốn theo dõi..."  autocomplete="off" class="class_text_autocomplete ac_input txt-symbol" />'),
            (l +=
                '<a href="javascript:void(0);" id="btn_addsymbol" class="btn-addsymbol"></a></div>'),
            (l += "</div>"),
            (l +=
                '<div class="popup-row list-wrapper" id="CafeF_StockSymbolSlidePopupList"></div>'),
            (l +=
                '<div class="popup-row"><a href="javascript:void(0);" id="btn_removesymbol" class="btn-removesymbol"><i class="ico-remove"></i>Xóa toàn bộ</a></div>'),
            (l += '<div class="clearfix" id="topprice-placeholder"></div>'),
            (l += "</div></div>"),
            jQuery('[data-type="stock-container"]').append(l),
            jQuery("#CafeF_StockSymbolSlidePopup")
                .find("#btn_addsymbol")
                .unbind("click")
                .bind("click", function () {
                    i.AddSymbol();
                }),
            jQuery("#CafeF_StockSymbolSlidePopup")
                .find("#btn_removesymbol")
                .unbind("click")
                .bind("click", function () {
                    i.RemoveAllSymbols();
                }),
            i.GetCookies(i.CookiesName) &&
            (i.GetCookies(i.CookiesName).indexOf("@") >= 0
                ? i.GetSymbolListFromCookies_OldVersion()
                : i.GetSymbolListFromCookies());
        var a = i.GetCookies(i.StateCookiesName);
        a
            ? "1" == (a = a.replace("@", ""))
                ? i.ShowSlide()
                : i.HideSlide()
            : i.ShowSlide(),
            $("#CafeF_StockSymbolContainer").hasClass("active") &&
            i.OpenPopup("none");
    },

    MigrateFavoriteStocksCookie: function () {
        var name = this.CookiesName;
        var value = this.GetCookies(name);
        if (!value && typeof oc === 'undefined') return;
        // delete all variants (no domain, cafef.vn, .cafef.vn) then set unified
        var past = new Date(0).toUTCString();
        try { document.cookie = name + "=; expires=" + past + ";path=/"; } catch (ex) { }
        try { document.cookie = name + "=; expires=" + past + ";path=/;domain=cafef.vn"; } catch (ex) { }
        try { document.cookie = name + "=; expires=" + past + ";path=/;domain=.cafef.vn"; } catch (ex) { }
        if (value) {
            this.SetCookie(name, value, this.bm_st_time_exp);
        }
    },

    GetSymbolListFromCookies: function () {
        var t = this;
        t.display_list = "";
        t.symbol_list = t.GetCookies(t.CookiesName);
        if ("" != t.symbol_list) {
            // Migration V3: Đảm bảo cả Cookie và LocalStorage đều theo thứ tự "mới lên đầu"
            if (!localStorage.getItem('cafef_watchlist_migrated_v3')) {
                // Đảo ngược Cookie
                t.symbol_list = t.symbol_list.split(';').reverse().join(';');
                t.SetCookie(t.CookiesName, t.symbol_list, t.bm_st_time_exp);

                // Đảo ngược cả LocalStorage nếu có
                const saved = localStorage.getItem('cafef_watchlist');
                if (saved) {
                    try {
                        const stocks = JSON.parse(saved);
                        if (Array.isArray(stocks)) {
                            localStorage.setItem('cafef_watchlist', JSON.stringify(stocks.reverse()));
                        }
                    } catch (e) { }
                }

                localStorage.setItem('cafef_watchlist_migrated_v3', 'true');

            }
            for (
                var e = t.symbol_list.split(";"), i = 0;
                i < e.length && i < t.MaxSymbolsDisplay;
                i++
            )
                t.display_list += ";" + e[i];
            "" != t.display_list &&
                (t.display_list = t.display_list.substring(1));
        } else t.display_list = "";
    },
    GetSymbolListFromCookies_OldVersion: function () {
        var t = this,
            e = t.GetCookies(t.CookiesName);
        if ("" != e) {
            for (var i = e.split("@"), o = 0; o < i.length; o++)
                if ("" != i[o]) {
                    var s = i[o].split("|");
                    t.symbol_list += ";" + s[1];
                }
            "" != t.symbol_list && (t.symbol_list = t.symbol_list.substring(1));
            for (
                var l = t.symbol_list.split(";"), o = 0;
                o < l.length && o < t.MaxSymbolsDisplay;
                o++
            )
                t.display_list += ";" + l[o];
            "" != t.display_list &&
                (t.display_list = t.display_list.substring(1));
        } else t.display_list = "";
    },
    HideSlide: function () {
        var t = this;
        jQuery("#CafeF_StockSymbolSlideTable").hide(),
            jQuery("#CafeF_StockSymbolSlideTable_Hide").show(),
            t.SetCookie(t.StateCookiesName, 0, t.bm_st_state_time_exp);
    },
    ShowSlide: function () {
        var t = this;
        jQuery("#CafeF_StockSymbolSlideTable").show(),
            jQuery("#CafeF_StockSymbolSlideTable_Hide").hide(),
            t.SetCookie(t.StateCookiesName, 1, t.bm_st_state_time_exp);
    },
    LoadSymbolData: function (t) {
        const self = this;
        if (self.display_list) {
            try {
                fetch(`https://cafef.vn/du-lieu/Ajax/PageNew/RealtimePricesHeader.ashx?symbols=${self.display_list}`)
                    .then((resData) => {
                        if (resData.status !== 500) {
                            return resData.json();
                        }
                        else {
                            throw new Error('Parameter is not a number!');
                        }
                    })
                    .then((data) => {
                        let Symbols = [];
                        Symbols = Object.keys(data).map((key) => {
                            const priceChange = data[key].Price - data[key].RefPrice;
                            const pricePercent = (priceChange / data[key].RefPrice) * 100;
                            return {
                                Symbol: key || '--',
                                Datas: [
                                    data[key].Price,
                                    priceChange,
                                    pricePercent,
                                    data[key].CeilingPrice,
                                    data[key].FloorPrice,
                                ],
                            }
                        })

                        self.OnLoaded({ Symbols }, "StockSymbolSlide");
                    }).catch((error) => {
                    })
            } catch (error) {
            }
        }
    },
    OnLoaded: function (data, methodName) {
        var self = this, json = eval(data);

        if (
            (json &&
                json.ListDoanhNghiep &&
                "2" == self.TabTinMoi &&
                json.ListDoanhNghiep.length >= 1 &&
                "0" != json.ListDoanhNghiep[0].News_ID &&
                self.ProcessDataResponseBelow(json.ListDoanhNghiep, self.LastUpdateTinMoi),
                json &&
                json.HeaderBox &&
                null != typeof json.HeaderBox &&
                $("div#headerleftindex").html(json.HeaderBox),
                json && json.Symbols)
        ) {
            for (
                var output = "",
                displayList = self.display_list.split(";"),
                i = 0,
                j = 0,
                maxdisp = self.MaxSymbolsDisplay;
                i < maxdisp;
            ) {
                try {
                    var displayIndex = 1e3, _symTitle = "";

                    if (i < json.Symbols.length) {
                        const listSymbol = ['HSX', 'HNX', 'UPCOM', 'HSXD', 'HNXD', 'UPCD', 'VN30', 'VN30D'];
                        if (listSymbol.includes(json.Symbols[i].Symbol)) {
                            i++, maxdisp++;
                            continue;
                        }

                        for (
                            displayIndex = 0;
                            displayIndex < displayList.length &&
                            displayList[displayIndex] != json.Symbols[i].Symbol;
                            displayIndex++
                        );

                        var image = "nochange.gif",
                            style = "NoChange",
                            _class = "number",
                            _spanIcon = '<span class="icon_up2 sprite"></span>',
                            _class = "FloatRight",
                            sign = "";

                        // UP / DOWN theo Change
                        if (json.Symbols[i].Datas[self.Fields.Change] > 0) {
                            image = "up.gif";
                            style = "Up";
                            sign = "+";
                            // _spanIcon = '<span class="icon_up sprite"></span>';
                            _spanIcon = '<span class="arrow-up"></span>';
                            _class = "FloatRight up";
                        }
                        else if (json.Symbols[i].Datas[self.Fields.Change] < 0) {
                            image = "down.gif";
                            style = "Down";
                            // _spanIcon = '<span class="icon_down sprite"></span>';
                            _spanIcon = '<span class="arrow-down"></span>';
                            _class = "FloatRight down";
                        }

                        // 🔥 OVERRIDE nếu TRẦN / SÀN
                        if (json.Symbols[i].Datas[self.Fields.ceiling] > 0 && json.Symbols[i].Datas[self.Fields.ceiling] == json.Symbols[i].Datas[self.Fields.Price]) {
                            style = "Ceiling";
                            sign = "+";
                            // _spanIcon = '<span class="icon_up sprite"></span>';
                            _spanIcon = '<span class="arrow-up"></span>';
                            _class = "FloatRight ceiling";
                        }
                        else if (json.Symbols[i].Datas[self.Fields.floor] > 0 && json.Symbols[i].Datas[self.Fields.floor] == json.Symbols[i].Datas[self.Fields.Price]) {
                            style = "Floor";
                            // _spanIcon = '<span class="icon_down sprite"></span>';
                            _spanIcon = '<span class="arrow-down"></span>';
                            _class = "FloatRight floor";
                        }

                        (output =
                            '<table width="100%" cellspacing="0" cellpadding="0" border="0"><tr><td>'),
                            (output +=
                                '<div class="FloatLeft" title="' + GetCompanyInfoLink(json.Symbols[i].Symbol) + '" style="display: flex;max-width: calc(100% - 15px);margin-bottom: -3px; margin-left: -1px;"><a href="' +
                                GetCompanyInfoLink(json.Symbols[i].Symbol) +
                                '"><b style="margin-bottom: 3px;margin-left: 3px;overflow: hidden;display: inline-block;max-width: 30px;text-overflow: ellipsis;white-space: nowrap;">' +
                                json.Symbols[i].Symbol +
                                "</b></a>"),
                            (output +=
                                '<div class="Price" id="slide_price_' +
                                json.Symbols[i].Symbol +
                                '" style="display: inline;">' +
                                self.FormatNumber(
                                    json.Symbols[i].Datas[self.Fields.Price],
                                    !0
                                ) +
                                "</div>"),
                            (output += "</div>"),
                            (output +=
                                '<div class="FloatRight"><span class="sprite clear_mack" title="Xóa mã CK này khỏi danh sách" onclick="' +
                                self.instance_name +
                                ".RemoveSymbol('" +
                                json.Symbols[i].Symbol +
                                "')\"></span></div>"),
                            (output += "</td></tr><tr><td>"),


                            (output +=
                                '<div class="' + _class + '"' + 'id="slide_change_' + json.Symbols[i].Symbol + '">' +
                                _spanIcon +
                                '<span class="' +
                                style +
                                '" id="slide_change_' +
                                json.Symbols[i].Symbol +
                                '">' +
                                sign +
                                self.FormatNumber(
                                    json.Symbols[i].Datas[self.Fields.Change],
                                    !0
                                ) +
                                '</span> <span class="' +
                                style +
                                '" id="slide_percent_' +
                                json.Symbols[i].Symbol +
                                '">(' +
                                sign +
                                self.FormatNumber(
                                    json.Symbols[i].Datas[
                                    self.Fields.ChangePercent
                                    ],
                                    !0
                                ) +
                                "%)</span></div>"),
                            (output += "</td></tr></table>"),
                            (self.staticData[json.Symbols[i].Symbol] = {
                                Price: self.FormatNumber(
                                    json.Symbols[i].Datas[self.Fields.Price],
                                    !0
                                ),
                                Change:
                                    _spanIcon +
                                    '<span class="' +
                                    style +
                                    '" id="slide_change_' +
                                    json.Symbols[i].Symbol +
                                    '">' +
                                    sign +
                                    self.FormatNumber(
                                        json.Symbols[i].Datas[
                                        self.Fields.Change
                                        ],
                                        !0
                                    ) +
                                    '</span> <span class="' +
                                    style +
                                    '" id="slide_percent_' +
                                    json.Symbols[i].Symbol +
                                    '">(' +
                                    sign +
                                    self.FormatNumber(
                                        json.Symbols[i].Datas[
                                        self.Fields.ChangePercent
                                        ],
                                        !0
                                    ) +
                                    "%)</span>",
                            }),
                            $(
                                '[data-type="price"][data-symbol="' +
                                json.Symbols[i].Symbol +
                                '"]'
                            ).text(
                                self.staticData[json.Symbols[i].Symbol].Price
                            ),
                            $(
                                '[data-type="change"][data-symbol="' +
                                json.Symbols[i].Symbol +
                                '"]'
                            ).html(
                                self.staticData[json.Symbols[i].Symbol].Change
                            ),
                            (_symTitle = GetCompanyName(
                                json.Symbols[i].Symbol
                            )),
                            self.UpdateCell(displayIndex, output, _symTitle);
                    }
                } catch (t) {

                }
                i++;
            }
            for (var i = 0; i < json.Symbols.length; i++)
                if (
                    "HSX" == json.Symbols[i].Symbol ||
                    "HNX" == json.Symbols[i].Symbol ||
                    "UPCOM" == json.Symbols[i].Symbol ||
                    "VN30" == json.Symbols[i].Symbol
                ) {
                    var _center = "1";
                    "HNX" == json.Symbols[i].Symbol
                        ? (_center = "2")
                        : "UPCOM" == json.Symbols[i].Symbol
                            ? (_center = "9")
                            : "VN30" == json.Symbols[i].Symbol && (_center = "11");
                    try {
                        var datas = json.Symbols[i].Datas,
                            _bidx =
                                $(".idx_" + _center).html() !=
                                datas[0].toString(),
                            _bidc =
                                $(".idc_" + _center).html() !=
                                datas[1].toString(),
                            _bidp =
                                $(".idp_" + _center).html() !=
                                datas[2].toString() + "%",
                            _bidv =
                                $(".idv_" + _center).html() !=
                                datas[3].toString();
                        $(".idx_" + _center).html(datas[0].toString()),
                            $(".idc_" + _center).html(datas[1].toString()),
                            $(".idp_" + _center).html(
                                datas[2].toString() + "%"
                            ),
                            $(".idv_" + _center).html(datas[3].toString()),
                            $(".idt_" + _center).html(datas[4].toString()),
                            $(".idx_" + _center)
                                .parents(".index_ck")
                                .removeClass("up")
                                .removeClass("down")
                                .addClass(
                                    datas[1].toString().indexOf("-") >= 0
                                        ? "down"
                                        : "up"
                                ),
                            $(".idc_" + _center)
                                .parents("#idxd_" + _center)
                                .removeClass("Index_Up")
                                .removeClass("Index_Down")
                                .addClass(
                                    datas[1].toString().indexOf("-") >= 0
                                        ? "Index_Down"
                                        : "Index_Up"
                                ),
                            $(".img_" + _center).attr(
                                "src",
                                "http://cafef3.mediacdn.vn/images/" +
                                (datas[1].toString().indexOf("-") >= 0
                                    ? "btdown"
                                    : "btup") +
                                ".gif"
                            );
                        var _class =
                            datas[1].toString().indexOf("-") >= 0
                                ? "down"
                                : 0 == datas[1].toString().indexOf("0")
                                    ? "normal"
                                    : "up";
                        $(".con_" + _center).attr(
                            "class",
                            "con_" + _center + " " + _class
                        ),
                            _bidx &&
                            $(".idx_" + _center).css(
                                "background-color",
                                "#FF6A00"
                            ),
                            _bidc &&
                            $(".idc_" + _center).css(
                                "background-color",
                                "#FF6A00"
                            ),
                            _bidp &&
                            $(".idp_" + _center).css(
                                "background-color",
                                "#FF6A00"
                            ),
                            _bidv &&
                            $(".idv_" + _center).css(
                                "background-color",
                                "#FF6A00"
                            ),
                            window.setTimeout(
                                "$('.idx_" +
                                _center +
                                ",.idc_" +
                                _center +
                                ",.idp_" +
                                _center +
                                ",.idv_" +
                                _center +
                                "').css('background-color', '');",
                                1e3
                            );
                    } catch (t) {

                    }
                } else {
                    if (
                        "HSXD" != json.Symbols[i].Symbol &&
                        "HNXD" != json.Symbols[i].Symbol &&
                        "UPCD" != json.Symbols[i].Symbol &&
                        "VN30D" != json.Symbols[i].Symbol
                    )
                        continue;
                    var _center = "1";
                    "HNXD" == json.Symbols[i].Symbol
                        ? (_center = "2")
                        : "UPCD" == json.Symbols[i].Symbol
                            ? (_center = "9")
                            : "VN30D" == json.Symbols[i].Symbol && (_center = "11");
                    var datas = json.Symbols[i].Datas,
                        _stats = datas[2].toString().split("|"),
                        _bivl =
                            $(".ivl_" + _center).html() != datas[0].toString(),
                        _bidf =
                            $(".idf_" + _center).html() != datas[1].toString(),
                        _bceiling =
                            $(".ceiling_" + _center).html() !=
                            _stats[0].toString(),
                        _bup =
                            $(".up_" + _center).html() != _stats[1].toString(),
                        _bnormal =
                            $(".normal_" + _center).html() !=
                            _stats[2].toString(),
                        _bdown =
                            $(".down_" + _center).html() !=
                            _stats[3].toString(),
                        _bfloor =
                            $(".floor_" + _center).html() !=
                            _stats[4].toString();
                    $(".ivl_" + _center).html(datas[0].toString()),
                        $(".idf_" + _center).html(datas[1].toString()),
                        $(".ceiling_" + _center).html(_stats[0].toString()),
                        $(".up_" + _center).html(_stats[1].toString()),
                        $(".normal_" + _center).html(_stats[2].toString()),
                        $(".down_" + _center).html(_stats[3].toString()),
                        $(".floor_" + _center).html(_stats[4].toString()),
                        $(".ifb_" + _center).html(datas[3].toString()),
                        $(".ifs_" + _center).html(datas[4].toString()),
                        _bivl &&
                        $(".ivl_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bidf &&
                        $(".idf_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bceiling &&
                        $(".ceiling_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bup &&
                        $(".up_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bnormal &&
                        $(".normal_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bdown &&
                        $(".down_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        _bfloor &&
                        $(".floor_" + _center).css(
                            "background-color",
                            "#FF6A00"
                        ),
                        window.setTimeout(
                            "$('.idf_" +
                            _center +
                            ",.ivl_" +
                            _center +
                            ",.ceiling_" +
                            _center +
                            ",.up_" +
                            _center +
                            ",.normal_" +
                            _center +
                            ",.down_" +
                            _center +
                            ",.floor_" +
                            _center +
                            "').css('background-color', '');",
                            1e3
                        );
                }
        }
    },
    OpenPopup: function (t) {
        var e = this;
        try {
            if (typeof oc !== "undefined" && jQuery && jQuery.fn && jQuery.fn.autocomplete) {
                jQuery("#CafeF_StockSymbolSlideKeyword").autocomplete(oc, {
                    minChars: 1,
                    delay: 10,
                    width: 300,
                    matchContains: !0,
                    autoFill: !1,
                    max: 5,
                    formatItem: function (t) {
                        return t.c + " - " + t.m + "@" + t.o;
                    },
                    formatResult: function (t) {
                        return t.c + " - " + t.m;
                    },
                    isAddSymbolToFavorite: !0,
                    CafeF_StockSymbolSlideObject: e,
                });
            }
        } catch (ex) { }
        e.RefreshListOfSymbolInConfigWindow(),
            "none" == t
                ? jQuery("#CafeF_StockSymbolSlidePopup").stop(!0, !0).show()
                : jQuery("#CafeF_StockSymbolSlidePopup").stop(!0, !0).slideDown("fast"),
            jQuery("#CafeF_StockSymbolSlideKeyword").val("").focus(),
            jQuery("#CafeF_StockSymbolContainer").addClass("active"),
            jQuery("#CafeF_StockSymbolContainer .icon_dropdown").addClass(
                "active"
            );
    },
    ClosePopup: function () {
        jQuery("#CafeF_StockSymbolSlideKeyword").val(""),
            jQuery("#CafeF_StockSymbolSlidePopup").stop(!0, !0).slideUp("fast"),
            jQuery("#CafeF_StockSymbolContainer").removeClass("active"),
            jQuery("#CafeF_StockSymbolContainer .icon_dropdown").removeClass(
                "active"
            );
    },
    MoveLeft: function () {
        var t = this;
        if (0 != t.symbol_list.indexOf(t.display_list) && "" != t.displayList) {
            var e = t.symbol_list.split(";"),
                i = t.display_list.split(";"),
                o = 0;
            for (o = 0; o < e.length && e[o] != i[0]; o++);
            t.display_list = "";
            for (
                var s = o - 1, l = 0;
                s < e.length && l < t.MaxSymbolsDisplay;
                s++
            )
                (t.display_list += ";" + e[s]), l++;
            "" != t.display_list &&
                (t.display_list = t.display_list.substring(1));
            t.LoadSymbolData(!0);
        }
    },
    MoveRight: function () {
        var t = this;
        if (
            t.symbol_list.indexOf(t.display_list) + t.display_list.length !=
            t.symbol_list.length &&
            "" != t.displayList
        ) {
            var e = t.symbol_list.split(";"),
                i = t.display_list.split(";"),
                o = 0;
            for (o = 0; o < e.length && e[o] != i[0]; o++);
            t.display_list = "";
            for (
                var s = o + 1, l = 0;
                s < e.length && l < t.MaxSymbolsDisplay;
                s++
            )
                (t.display_list += ";" + e[s]), l++;
            "" != t.display_list &&
                (t.display_list = t.display_list.substring(1));
            t.LoadSymbolData(!0);
        }
    },
    AddSymbolToFavorite: function (t) {
        if (t && t.toUpperCase().indexOf("INDEX") !== -1) {
            var o = document.getElementById("CafeF_StockSymbolSlideKeyword");
            if (o) o.value = "";
            return;
        }
        var e,
            i = this,
            o = document.getElementById("CafeF_StockSymbolSlideKeyword");
        if ("" != i.symbol_list) {
            e = i.symbol_list.split(";");
            for (s = 0; s < e.length; s++) {
                if (e[s]?.toUpperCase() == t?.toUpperCase()) {
                    // Nếu đã có, đưa lên đầu
                    e.splice(s, 1);
                    i.symbol_list = t.toUpperCase() + (e.length > 0 ? ";" + e.join(";") : "");
                    i.SetCookie(i.CookiesName, i.symbol_list, i.bm_st_time_exp);
                    i.LoadSymbolData(!0);
                    i.RefreshListOfSymbolInConfigWindow();
                    if (o) o.value = "";
                    return;
                }
            }
            if (e.length >= i.MaxSymbolsInQueue)
                return (
                    alert(
                        "Đã đủ " +
                        i.MaxSymbolsInQueue +
                        " mã CK trong danh sách theo dõi"
                    ),
                    void (o.value = "")
                );
            i.symbol_list = t.toUpperCase() + ";" + i.symbol_list;
        } else i.symbol_list = t.toUpperCase();
        if ((e = i.symbol_list.split(";")).length <= i.MaxSymbolsDisplay)
            i.display_list = i.symbol_list;
        else {
            i.display_list = "";
            for (var s = 0; s < i.MaxSymbolsDisplay && s < e.length; s++)
                i.display_list += ";" + e[s];
            "" != i.display_list &&
                (i.display_list = i.display_list.substring(1));
        }
        i.SetCookie(i.CookiesName, i.symbol_list, i.bm_st_time_exp),
            i.LoadSymbolData(!0),
            i.RefreshListOfSymbolInConfigWindow(),
            (o.value = "");
        const mckTG = t.toUpperCase();
        if (mckTG) this.joiRoom(mckTG);
    },
    RemoveAllSymbols: function () {
        this.leaveAllRoom();
        var t = this;
        (t.display_list = ""),
            (t.symbol_list = ""),
            t.SetCookie(t.CookiesName, t.symbol_list, t.bm_st_time_exp),
            t.InitSlideTemplate(t.containerId),
            t.RefreshListOfSymbolInConfigWindow();
        var e = document.getElementById("CafeF_StockSymbolSlideKeyword");
        (e.value = ""), e.focus(), (t.staticData = []);
    },
    RemoveSymbol: function (t) {
        var e = this,
            i = ";" + e.display_list + ";",
            o = e.symbol_list.split(";");
        e.symbol_list = "";
        var s = -1;
        (e.display_list = ";" + e.display_list + ";"),
            (e.display_list = e.display_list.replace(";" + t + ";", ";")),
            (e.display_list = e.display_list.substring(
                1,
                e.display_list.length - 1
            ));
        for (
            var l =
                "" == e.display_list
                    ? ""
                    : e.display_list.substring(
                        e.display_list.lastIndexOf(";") + 1
                    ),
            a = 0,
            n = -1;
            a < o.length;
            a++
        )
            o[a] != t &&
                (n++,
                    "" != l && -1 == s && o[a] == l && (s = n),
                    (e.symbol_list += ";" + o[a]));
        if (
            ("" != e.symbol_list &&
                (e.symbol_list = e.symbol_list.substring(1)),
                (o = e.symbol_list.split(";")),
                s < e.MaxSymbolsDisplay && o > e.MaxSymbolsDisplay && s++,
                i.indexOf(";" + t + ";") >= 0)
        ) {
            0 == e.symbol_list.indexOf(e.display_list) &&
                o.length > e.MaxSymbolsDisplay &&
                s++,
                (e.display_list = "");
            for (a = 0; a < e.MaxSymbolsDisplay && s >= 0; a++)
                (e.display_list = ";" + o[s] + e.display_list), s--;
        }
        "" != e.display_list && (e.display_list = e.display_list.substring(1)),
            e.SetCookie(e.CookiesName, e.symbol_list, e.bm_st_time_exp),
            e.InitSlideTemplate(e.containerId),
            e.LoadSymbolData(!0),
            e.RefreshListOfSymbolInConfigWindow();
        var r = document.getElementById("CafeF_StockSymbolSlideKeyword");
        r.value = "";
        try {
            r.focus();
        } catch (t) { }
        e.leaveRoom(t);
    },
    RefreshListOfSymbolInConfigWindow: function () {
        //render table popup
        var t = this,
            e = "";
        if ("" != t.symbol_list) {
            e =
                '<table align="center" width="90%" border="0" cellpadding="3" cellspacing="0">';
            for (var i = t.symbol_list.split(";"), o = 0; o < i.length; o++) {
                var s = "",
                    l = "",
                    a = t.staticData[i[o]];
                a && ((s = a.Price), (l = a.Change)),
                    (e += "<tr>"),
                    (e +=
                        '<td style="border:none;"><span style="color: #aaaaaa">' +
                        (o + 1) +
                        ".</span> <strong>" +
                        i[o] +
                        "</strong></td>"),
                    (e +=
                        '<td data-type="price" data-symbol="' +
                        i[o] +
                        '" style="border:none;">' +
                        s +
                        "</td>"),
                    (e +=
                        '<td data-type="change" data-symbol="' +
                        i[o] +
                        '" style="border:none;">' +
                        l +
                        "</td>"),
                    (e +=
                        '<td style="border:none;" align="right"><img alt="Xóa mã CK khỏi danh sách" onclick="' +
                        t.instance_name +
                        ".RemoveSymbol('" +
                        i[o] +
                        '\')" src="' +
                        t.image_folder +
                        '/delete.gif" /></td>'),
                    (e += "</tr>");
            }
            e += "</table>";
        }
        jQuery("#CafeF_StockSymbolSlidePopupList").html(e);
    },
    FormatNumber: function (t, e) {
        if ("" == t) return e ? "0" : "";
        try {
            return (t = CafeF_FormatNumber(parseFloat(t), 2, ".", ","));
        } catch (t) {
            return e ? "0" : "";
        }
    },
    UpdateCell: function (t, e, i) {
        var o = this,
            s = $("#" + o.containerId).find("li.wait:eq(" + t + ")");
        e.toString().indexOf("table") > 0
            ? s.unbind("click")
            : s.unbind("click").bind("click", function () {
                o.OpenPopup();
            }),
            s.attr("title", i),
            s.html(e),
            (o.OldCellDatas[t] = e);
    },
    CreateScriptObject: function (t, e) {
        var i = this;
        e && i.script_object && i.RemoveScriptObject(),
            (i.script_object = document.createElement("script")),
            i.script_object.setAttribute("type", "text/javascript"),
            i.script_object.setAttribute("src", t),
            document
                .getElementsByTagName("head")[0]
                .appendChild(i.script_object);
    },
    RemoveScriptObject: function () {
        var t = this;
        t.script_object.parentNode.removeChild(t.script_object),
            (t.script_object = null);
    },
    SetCookie: function (t, e, i) {
        var o = new Date();
        o.setDate(o.getDate() + i),
            (document.cookie =
                t +
                "=" +
                escape(e) +
                (null == i ? "" : ";expires=" + o.toGMTString()) +
                ";path=/;domain=.cafef.vn;");
    },
    GetCookies: function (t) {
        if (document.cookie.length > 0) {
            var e = document.cookie.indexOf(t + "=");
            if (-1 != e) {
                e = e + t.length + 1;
                var i = document.cookie.indexOf(";", e);
                return (
                    -1 == i && (i = document.cookie.length),
                    unescape(document.cookie.substring(e, i))
                );
            }
        }
        return "";
    },
    async SignalRInit() {
        this.sigNalR = window.cfTradeRealTime
        this.joiAllRoom();
        this.onListenMessage();
    },
    joiRoom(mck) {
        const { action, hub, type } = this.sigNalRConfig
        this.sigNalR.signalrMessageHub.reqAction(type.invoke, hub.priceHub, null, action.joinChannel, mck)
    },
    onListenMessage() {
        const self = this;
        const { action, hub, type } = this.sigNalRConfig;
        this.sigNalR.signalrMessageHub.reqAction(type.on, hub.priceHub, (data) => {
            if (!data || data.price == null || data.refPrice == null) {
                return;
            }
            const price = Number(data.price);
            const refPrice = Number(data.refPrice);
            if (!Number.isFinite(price) || !Number.isFinite(refPrice) || refPrice === 0) {
                return;
            }
            const priceChange = price - refPrice;
            const pricePercent = (priceChange / refPrice) * 100;
            const prevItem = self.curentData[data.symbol];
            const curentItem = {
                Symbol: data.symbol,
                Datas: [
                    price.toFixed(2),
                    priceChange,
                    pricePercent,
                ],
            }
            if (!curentItem.Datas.some((e, i) => e === prevItem?.Datas[i])) {
                self.curentData[data.symbol] = curentItem;
                self.OnLoaded(
                    {
                        Symbols: [
                            curentItem,
                        ],
                    },
                    "StockSymbolSlide"
                );
            }
        }, action.RealtimePrice)
    },
    leaveRoom(mck) {
        const { action, hub, type } = this.sigNalRConfig;
        if (mck) this.sigNalR.signalrMessageHub.reqAction(type.invoke, hub.priceHub, null, action.leaveChannel, mck);
    },
    joiAllRoom() {
        const list = this.display_list.split(";");
        list.length > 0 &&
            list.forEach((item) => {
                if (item) this.joiRoom(item);
            });
    },
    leaveAllRoom() {
        const list = this.display_list.split(";");
        list.length > 0 &&
            list.forEach((item) => {
                this.leaveRoom(item);
            });
    },
};
$(document).ready(function () {
    try {
        loadBoxChungKhoan();
    } catch (e) { }
    try {
        if ($ && $.fn && $.fn.slimScroll) {
            $("#divTinMoi").slimScroll({
                height: "124px",
            });
        }
    } catch (e) { }
    try {
        CafeF_StockSymbol.init();
    } catch (e) { }
    try {
        slimScrollBoxTinMois();
    } catch (e) { }
});

// Key lưu trữ trong localStorage
// const WATCHLIST_KEY = 'cafef_watchlist';
window.CafeF = window.CafeF || {};
window.CafeF.Storage = window.CafeF.Storage || {};
window.CafeF.Storage.WATCHLIST_KEY = CafeF.Storage.WATCHLIST_KEY || 'cafef_watchlist';
// Flag để ngăn save khi đang restore hoặc chưa khởi tạo xong
window.CafeF.Storage.isRestoring = window.CafeF.Storage.isRestoring || false;
window.CafeF.Storage.hasInitialized = window.CafeF.Storage.hasInitialized || false;

// Hàm lưu watchlist vào localStorage   
function saveWatchlist() {
    // Không save khi chưa khởi tạo xong hoặc đang restore
    if (!window.CafeF.Storage.hasInitialized || window.CafeF.Storage.isRestoring) {

        return;
    }

    // Ưu tiên lấy từ symbol_list là nguồn dữ liệu chính
    let stocks = [];
    if (typeof CafeF_StockSymbol !== 'undefined' && CafeF_StockSymbol.symbol_list) {
        stocks = CafeF_StockSymbol.symbol_list.split(';').filter(s => s && s.trim());
    } else {
        // Fallback đọc từ DOM nếu object chưa có (hiếm khi xảy ra ở bước này)
        const container = document.getElementById('macktheodoi');
        if (container) {
            container.querySelectorAll('span.clear_mack[onclick]').forEach(function (span) {
                const onclick = span.getAttribute('onclick');
                const match = onclick.match(/RemoveSymbol\(['"]([^'"]+)['"]\)/);
                if (match && match[1]) {
                    stocks.push(match[1]);
                }
            });
        }
    }

    localStorage.setItem('cafef_watchlist', JSON.stringify(stocks));

}

// Hàm khôi phục watchlist từ localStorage
function loadWatchlist(callback) {
    const saved = localStorage.getItem('cafef_watchlist');
    if (!saved) {

        if (callback) callback();
        return;
    }

    try {
        const stocks = JSON.parse(saved);
        if (stocks.length === 0) {

            if (callback) callback();
            return;
        }

        // Giữ nguyên thứ tự từ Storage (đã là Mới -> Cũ)
        // Khi restore, ta gọi AddSymbolToFavorite cho từng mã từ Cũ đến Mới
        // để kết quả cuối cùng là Mới nằm trên đầu.
        stocks.slice().reverse().forEach(function (symbol, index) {
            // Delay mỗi symbol một chút để tránh race condition
            setTimeout(function () {
                try {
                    // Kiểm tra xem symbol đã tồn tại trong list hiện tại chưa để tránh đảo thứ tự vô ích
                    const currentList = (CafeF_StockSymbol.symbol_list || "").split(";");
                    if (currentList.includes(symbol.toUpperCase())) {
                        // Đã có rồi thì bỏ qua không add nữa để giữ thứ tự hiện tại của cookie
                        if (index === stocks.length - 1) {
                            window.CafeF.Storage.isRestoring = false;
                            if (callback) callback();
                        }
                        return;
                    }

                    if (typeof CafeF_StockSymbol !== 'undefined' && typeof CafeF_StockSymbol.AddSymbolToFavorite === 'function') {
                        CafeF_StockSymbol.AddSymbolToFavorite(symbol);

                    }
                } catch (e) {
                    console.error('Error adding symbol:', symbol, e);
                }

                // Kết thúc restore sau khi thêm symbol cuối cùng
                if (index === stocks.length - 1) {
                    setTimeout(function () {
                        window.CafeF.Storage.isRestoring = false;

                        if (callback) callback();
                    }, 500);
                }
            }, index * 200); // Delay 200ms giữa mỗi symbol
        });
    } catch (e) {
        console.error('Error loading watchlist:', e);
        window.CafeF.Storage.isRestoring = false;
        if (callback) callback();
    }
}

// Theo dõi thay đổi trong watchlist container
function observeWatchlistChanges() {
    const container = document.getElementById('macktheodoi');
    if (!container) return;

    const observer = new MutationObserver(function (mutations) {
        // Delay để đảm bảo DOM đã update xong
        setTimeout(saveWatchlist, 300);
    });

    observer.observe(container, {
        childList: true,
        subtree: true
    });
}

// Khởi tạo khi DOM ready
document.addEventListener('DOMContentLoaded', function () {
    // Đợi thư viện stock load xong rồi mới restore watchlist
    setTimeout(function () {
        // Quan trọng: Load watchlist TRƯỚC, rồi mới bắt đầu observe
        // Và chỉ set hasInitialized = true SAU KHI restore xong
        loadWatchlist(function () {
            // Callback này chạy sau khi restore hoàn thành
            window.CafeF.Storage.hasInitialized = true;
            observeWatchlistChanges();

        });
    }, 1000);
});

// Backup: cũng lưu khi rời trang
window.addEventListener('beforeunload', function () {
    if (window.CafeF.Storage.hasInitialized && !window.CafeF.Storage.isRestoring) {
        saveWatchlist();
    }
});