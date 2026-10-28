"""BanG Dream! 角色与声优生日内置列表。

每条记录字段：
    month, day   月、日（按 JST 循环，不带年份）
    kind         character | cv_live | cv_virtual | special | former_cv
    band         所属乐队
    position     乐队内位置
    char_name    角色名（character / cv_virtual / special / former_cv）
    cv_name      声优活动名（cv_live / cv_virtual / special / former_cv）
    message      专属文案；留空则走通用文案
    group        合并组；同日同组的条目作为一个发送单位，组内文案共用
    enabled      是否启用

约定：
    - 角色一律写真名（和奏瑞依，不写 Layer；朝日六花，不写 LOCK）
    - 声优一律写公开活动名（Raychell、夏芽、mika、Ayasa）
    - 梦限大MewType 以 VTuber 形式活动，只有角色条目
    - 美咲 / 米歇尔 同日，只保留美咲
    - 冰川日菜 / 冰川纱夜 同日，用 group="hikawa-twins" 绑定为一个单位
    - 同组只应在一条上写 message；有专属文案时整组只发这一条
    - 新增条目直接追加 B(...)，message 留空即可
"""


def B(month, day, kind, band, position, char_name="", cv_name="", message="", group=""):
    return {
        "month": month,
        "day": day,
        "kind": kind,
        "band": band,
        "position": position,
        "char_name": char_name,
        "cv_name": cv_name,
        "message": message,
        "group": group,
        "enabled": True,
    }


# 真人团：声优条目用 cv_live，主体只写声优活动名
LIVE_BANDS = frozenset({
    "Poppin'Party",
    "Roselia",
    "RAISE A SUILEN",
    "Morfonica",
    "MyGO!!!!!",
    "Ave Mujica",
    "梦限大MewType",
})

# 虚拟团：声优条目用 cv_virtual，主体写「角色的声优 声优名」
VIRTUAL_BANDS = frozenset({
    "Afterglow",
    "Pastel＊Palettes",
    "Hello, Happy World!",
    "millsage",
    "一家Dumb Rock!",
})


BUILTIN_BIRTHDAYS = [
    # 一月
    B(1, 2, "former_cv", "Roselia", "键盘手", "白金燐子", "明坂聪美"),
    B(1, 5, "cv_live", "MyGO!!!!!", "吉他手", "要乐奈", "青木阳菜"),
    B(1, 7, "character", "Afterglow", "键盘手", "羽泽鸫"),
    B(1, 13, "special", "RAISE A SUILEN", "主唱兼贝斯手", "和奏瑞依", "Raychell",message="今天是RAISE A SUILEN主唱和奏瑞依和Raychell的生日 转发说说到五个群切噜妈妈就会带着手作饭团来你家开live。我试过了，是假的，但是今天真的是切噜妈妈的生日，让我们祝她生日快乐"),
    B(1, 13, "cv_virtual", "Afterglow", "吉他手", "青叶摩卡", "三泽纱千香"),
    B(1, 14, "character", "Ave Mujica", "吉他手", "若叶睦"),
    B(1, 22, "cv_virtual", "millsage", "鼓手", "和泉朋花", "咲川雏乃"),
    B(1, 29, "cv_virtual", "Afterglow", "主唱兼吉他手", "美竹兰", "佐仓绫音"),
    # 二月
    B(2, 3, "cv_live", "RAISE A SUILEN", "吉他手", "朝日六花", "小原莉子"),
    B(2, 7, "character", "梦限大MewType", "节奏吉他手", "峰月律"),
    B(2, 8, "cv_live", "Roselia", "键盘手", "白金燐子", "志崎桦音"),
    B(2, 14, "character", "Ave Mujica", "键盘手", "丰川祥子"),
    B(2, 15, "cv_virtual", "millsage", "吉他手", "琴平凪", "结川麻希"),
    B(2, 18, "cv_live", "Ave Mujica", "吉他手", "若叶睦", "渡濑结月"),
    B(2, 19, "character", "Morfonica", "主唱", "仓田真白"),
    B(2, 22, "character", "MyGO!!!!!", "吉他手", "要乐奈"),
    B(2, 24, "cv_virtual", "millsage", "贝斯手", "滨崎茉幌", "伊驹祐里惠"),
    B(2, 28, "character", "Hello, Happy World!", "吉他手", "濑田薰"),
    # 三月
    B(3, 5, "special", "一家Dumb Rock!", "键盘手", "四宫宁月", "远野光"),
    B(3, 5, "cv_virtual", "一家Dumb Rock!", "吉他手兼主唱", "马桥心玖", "凉泉樱花"),
    B(3, 12, "character", "millsage", "键盘手兼主唱", "汐见萤"),
    B(3, 14, "cv_live", "MyGO!!!!!", "贝斯手", "长崎爽世", "小日向美香"),
    B(3, 15, "cv_virtual", "Hello, Happy World!", "鼓手", "松原花音", "丰田萌绘"),
    B(3, 16, "cv_live", "Roselia", "吉他手", "冰川纱夜", "工藤晴香"),
    B(3, 20, "character", "Pastel＊Palettes", "吉他手", "冰川日菜", group="hikawa-twins"),
    B(3, 20, "character", "Roselia", "吉他手", "冰川纱夜", group="hikawa-twins"),
    B(3, 23, "character", "Poppin'Party", "贝斯手", "牛込里美"),
    B(3, 25, "character", "RAISE A SUILEN", "键盘手", "鳰原令王那"),
    B(3, 26, "cv_live", "MyGO!!!!!", "主唱", "高松灯", "羊宫妃那"),
    B(3, 30, "character", "millsage", "吉他手", "伊泽枣"),
    B(3, 31, "cv_live", "Morfonica", "贝斯手", "广町七深", "西尾夕香"),
    # 四月
    B(4, 2, "character", "一家Dumb Rock!", "鼓手", "梅里千樱梨"),
    B(4, 6, "character", "Pastel＊Palettes", "贝斯手", "白鹭千圣"),
    B(4, 7, "character", "Ave Mujica", "贝斯手", "八幡海铃"),
    B(4, 10, "character", "Afterglow", "主唱兼吉他手", "美竹兰"),
    B(4, 10, "cv_virtual", "Hello, Happy World!", "DJ", "奥泽美咲", "黑泽朋世"),
    B(4, 10, "cv_virtual", "millsage", "吉他手", "伊泽枣", "千春"),
    B(4, 15, "character", "Afterglow", "鼓手", "宇田川巴"),
    B(4, 17, "character", "梦限大MewType", "主音吉他手", "宫永野乃花"),
    B(4, 17, "cv_live", "Morfonica", "吉他手", "桐谷透子", "直田姬奈"),
    B(4, 20, "cv_live", "Morfonica", "主唱", "仓田真白", "进藤天音"),
    # 五月
    B(5, 6, "character", "一家Dumb Rock!", "贝斯手", "矢仓蓬咲"),
    B(5, 11, "character", "Hello, Happy World!", "鼓手", "松原花音"),
    B(5, 12, "character", "RAISE A SUILEN", "鼓手", "佐藤益木"),
    B(5, 15, "cv_live", "MyGO!!!!!", "鼓手", "椎名立希", "林鼓子"),
    B(5, 19, "character", "Poppin'Party", "鼓手", "山吹沙绫"),
    B(5, 19, "cv_live", "Ave Mujica", "贝斯手", "八幡海铃", "冈田梦以"),
    B(5, 19, "cv_virtual", "一家Dumb Rock!", "鼓手", "梅里千樱梨", "菱川花菜"),
    B(5, 22, "cv_live", "RAISE A SUILEN", "键盘手", "鳰原令王那", "仓知玲凤"),
    B(5, 27, "character", "MyGO!!!!!", "贝斯手", "长崎爽世"),
    # 六月
    B(6, 1, "character", "Ave Mujica", "鼓手", "祐天寺若麦"),
    B(6, 16, "character", "Morfonica", "贝斯手", "广町七深"),
    B(6, 18, "cv_virtual", "Pastel＊Palettes", "鼓手", "大和麻弥", "中上育实"),
    B(6, 24, "cv_live", "Morfonica", "鼓手", "二叶筑紫", "mika"),
    B(6, 24, "former_cv", "Roselia", "贝斯手", "今井莉莎", "远藤祐里香"),
    B(6, 26, "character", "Ave Mujica", "主唱兼吉他手", "三角初华"),
    B(6, 27, "character", "Pastel＊Palettes", "键盘手", "若宫伊芙"),
    # 七月
    B(7, 3, "character", "Roselia", "鼓手", "宇田川亚子"),
    B(7, 5, "cv_live", "RAISE A SUILEN", "DJ", "珠手知由", "纺木吏佐"),
    B(7, 10, "cv_live", "MyGO!!!!!", "吉他手", "千早爱音", "立石凛"),
    B(7, 14, "character", "Poppin'Party", "主唱兼吉他手", "户山香澄"),
    B(7, 16, "character", "millsage", "贝斯手", "滨崎茉幌"),
    B(7, 16, "cv_virtual", "Afterglow", "鼓手", "宇田川巴", "日笠阳子"),
    B(7, 17, "character", "RAISE A SUILEN", "吉他手", "朝日六花"),
    B(7, 20, "cv_live", "RAISE A SUILEN", "鼓手", "佐藤益木", "夏芽"),
    B(7, 28, "character", "一家Dumb Rock!", "吉他手兼主唱", "须贺蕾叶"),
    B(7, 30, "character", "Hello, Happy World!", "贝斯手", "北泽育美"),
    # 八月
    B(8, 8, "character", "Hello, Happy World!", "主唱", "弦卷心"),
    B(8, 9, "character", "MyGO!!!!!", "鼓手", "椎名立希"),
    B(8, 10, "cv_virtual", "Pastel＊Palettes", "吉他手", "冰川日菜", "小泽亚李"),
    B(8, 16, "character", "梦限大MewType", "主唱", "仲町阿拉蕾"),
    B(8, 17, "cv_live", "Poppin'Party", "键盘手", "市谷有咲", "伊藤彩沙"),
    B(8, 18, "cv_virtual", "Hello, Happy World!", "贝斯手", "北泽育美", "吉田有里"),
    B(8, 25, "character", "Roselia", "贝斯手", "今井莉莎"),
    # 九月
    B(9, 3, "character", "Afterglow", "吉他手", "青叶摩卡"),
    B(9, 8, "character", "MyGO!!!!!", "吉他手", "千早爱音"),
    B(9, 10, "cv_live", "Ave Mujica", "键盘手", "丰川祥子", "高尾奏音"),
    B(9, 11, "cv_virtual", "millsage", "键盘手兼主唱", "汐见萤", "药师寺李有"),
    B(9, 12, "cv_live", "Roselia", "贝斯手", "今井莉莎", "中岛由贵"),
    B(9, 13, "cv_live", "Poppin'Party", "鼓手", "山吹沙绫", "大桥彩香"),
    B(9, 14, "cv_virtual", "Pastel＊Palettes", "键盘手", "若宫伊芙", "秦佐和子"),
    B(9, 15, "character", "Morfonica", "鼓手", "二叶筑紫"),
    B(9, 19, "character", "梦限大MewType", "键盘手", "藤都子"),
    # 十月
    B(10, 1, "character", "Hello, Happy World!", "DJ", "奥泽美咲"),
    B(10, 4, "character", "一家Dumb Rock!", "吉他手兼主唱", "马桥心玖"),
    B(10, 10, "cv_live", "Poppin'Party", "吉他手", "花园多惠", "大冢纱英"),
    B(10, 12, "cv_virtual", "Hello, Happy World!", "主唱", "弦卷心", "伊藤美来"),
    B(10, 17, "character", "Roselia", "键盘手", "白金燐子"),
    B(10, 17, "cv_live", "Roselia", "主唱", "凑友希那", "相羽爱奈"),
    B(10, 19, "cv_live", "Morfonica", "小提琴手", "八潮瑠唯", "Ayasa"),
    B(10, 23, "character", "Afterglow", "贝斯手", "上原绯玛丽"),
    B(10, 24, "character", "millsage", "鼓手", "和泉朋花",message="现在是东京时间 2026/10/24，也是 millsage 的鼓手，天才的追随者——和泉朋花的生日！转发这条消息到五个群，朋花就会带着 millsage 的大家会为你献上双手载满的幸福！我试过了，是假的，幸福不会因为转发消息就降临，但今天真的是朋花生日！让我们祝朋花生日快乐！🎂"),
    B(10, 24, "cv_live", "Roselia", "鼓手", "宇田川亚子", "樱川惠",message="现在是东京时间10月24日，是Roselia的鼓手，第一届lovelive大赛全国冠军的绮罗翼的声优樱川惠的生日，把这个消息转发到九个群，meguchi就会出现在你面前教你打鼓，我试过了是假的，但是翼队真的好帅R团的歌也好好听，所以今天真的是樱川惠的生日，让我们一起祝她事业顺利，生日快乐！"),
    B(10, 24, "cv_virtual", "一家Dumb Rock!", "贝斯手", "矢仓蓬咲", "花宫初奈",message="现在是日本时间10.24零点零分，是莲之空大小姐乙宗梢学姐、私立藤咲高中风纪委员长水鸟亚鸟学姐、家团贝斯手矢仓蓬咲的声优花宫初奈的生日，把这条消息转发到五个群聊，花宫初奈会到你面前让你做她的sweetie dog，我试过了是假的，还被人骂女声优痴，但今天真的是花宫初奈的生日，让我们祝她生日快乐！"),
    B(10, 25, "cv_live", "Poppin'Party", "贝斯手", "牛込里美", "西本里美",message="现在是北京时间10.25日，是Poppin'Party 的贝斯手牛込里美中之人西本里美的生日。转发这个消息到5个群，rimi就会出来请你吃巧克力螺包，我试过了，虽然是假的，还被人骂nsyc。但今天真的是rimiri的生日，祝rimiri生日快乐"),
    B(10, 26, "character", "Roselia", "主唱", "凑友希那",message="今天是10月26日，是Roselia的主唱，羽丘女高爱猫人士，知名今井莉莎单推，湊 友希那的生日，转发这个消息ykn就会教你唱歌，我试过了是假的还被骂不配待在这个乐队，但是今天真的是ykn的生日，让我们祝Roselia的主唱 湊友希那 生日快乐！"),
    B(10, 27, "character", "Poppin'Party", "键盘手", "市谷有咲",message="现在是东京时间10月27日0:00，是Poppin’party（悦动派对）最伟大的键盘手市谷有咲的生日，转发这个生日文案至5个群并留言秋妈妈秋妈妈秋豆麻袋秋豆，就会有一个黄发傲娇双马尾jk教你弹键盘。我试过了，是假的，但是今天真的是市谷有咲的生日，祝我们的傲娇键盘手生日快乐，其次就是ksar99"),
    # 十一月
    B(11, 3, "character", "Pastel＊Palettes", "鼓手", "大和麻弥",message="现在是东京时间11月3日0:00，是“狂乱的器材宅”大和麻弥的生日。“呼嘿嘿”将这段文案转发至15个群，就会在当天晚上收到MAYA亲手制作的蔬菜条套餐，我试过了。是假的，但今天真的是大和麻弥的生日！祝我们的设定最强鼓手生日快乐！"),
    B(11, 4, "character", "梦限大MewType", "DJ兼Mp", "千石由乃",message="现在是东京时间11月4日，是梦限大MewType的DJ兼MP（不是Mezzo Piano！）千石由乃的生日，把这条消息转发到5个群会收到千石悠亲笔签名的千石由乃vg卡，我试过了，是假的，还被别人说是打瓦打多了。另外giraffe不是大象或斑马。祝我们的cool beauty永远幸福，生日快乐！（已经被她钓翘嘴了……）"),
    B(11, 10, "cv_virtual", "Hello, Happy World!", "吉他手", "濑田薰", "田所梓",message="今天是hello happy world的吉他手濑田薰的中之人田所梓的生日，将这条消息转发到765个群kraz就会对你说76遍ありがthankyou然后骂你最低，我试过了这是假的但是我真的很想被kraz骂最低，虽然会被骂傻逼声优痴，但是今天真的是kraz生日，虽然这条发电消息又臭又长但是很感谢群友花11点45秒看，红豆泥，ありがthankyou，但是还是要说祝kraz生日快乐🎂🎂🎂"),
    B(11, 10, "cv_live", "Ave Mujica", "主唱兼吉他手", "三角初华", "佐佐木李子"),
    B(11, 19, "character", "Morfonica", "小提琴手", "八潮瑠唯"),
    B(11, 19, "cv_virtual", "一家Dumb Rock!", "吉他手兼主唱", "须贺蕾叶", "橘芽衣"),
    B(11, 22, "character", "MyGO!!!!!", "主唱", "高松灯"),
    B(11, 22, "cv_virtual", "Pastel＊Palettes", "主唱", "丸山彩", "前岛亚美"),
    B(11, 26, "cv_virtual", "Afterglow", "贝斯手", "上原绯玛丽", "加藤英美里"),
    # 十二月
    B(12, 4, "character", "Poppin'Party", "吉他手", "花园多惠"),
    B(12, 7, "character", "RAISE A SUILEN", "DJ", "珠手知由"),
    B(12, 10, "character", "millsage", "吉他手", "琴平凪"),
    B(12, 16, "character", "Morfonica", "吉他手", "桐谷透子"),
    B(12, 16, "cv_virtual", "Afterglow", "键盘手", "羽泽鸫", "金元寿子"),
    B(12, 19, "cv_virtual", "Pastel＊Palettes", "贝斯手", "白鹭千圣", "上坂堇"),
    B(12, 25, "cv_live", "Poppin'Party", "主唱兼吉他手", "户山香澄", "爱美"),
    B(12, 27, "character", "Pastel＊Palettes", "主唱", "丸山彩"),
    B(12, 31, "cv_live", "Ave Mujica", "鼓手", "祐天寺若麦", "米泽茜"),
]
