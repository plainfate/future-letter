#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""摘句：中英文的句子，离线内置，不需要联网。

每天按日期自动换一句；也可以点「换一句」往下翻，或按语言筛选。
收句子的标准：有明确出处、读起来有分量、不鸡汤。宁少勿滥。
"""

import hashlib
import secrets
from datetime import date

# (正文, 作者, 出处, 语言)
QUOTES_ZH = [
    # ---- 先秦诸子 ----
    ("人生天地之间，若白驹之过隙，忽然而已。", "庄子", "庄子·知北游", "zh"),
    ("吾生也有涯，而知也无涯。", "庄子", "庄子·养生主", "zh"),
    ("君子之交淡若水，小人之交甘若醴。", "庄子", "庄子·山木", "zh"),
    ("相濡以沫，不如相忘于江湖。", "庄子", "庄子·大宗师", "zh"),
    ("井蛙不可以语于海者，拘于虚也。", "庄子", "庄子·秋水", "zh"),
    ("天地有大美而不言。", "庄子", "庄子·知北游", "zh"),
    ("逝者如斯夫，不舍昼夜。", "孔子", "论语·子罕", "zh"),
    ("知之为知之，不知为不知，是知也。", "孔子", "论语·为政", "zh"),
    ("学而不思则罔，思而不学则殆。", "孔子", "论语·为政", "zh"),
    ("己所不欲，勿施于人。", "孔子", "论语·颜渊", "zh"),
    ("三人行，必有我师焉。", "孔子", "论语·述而", "zh"),
    ("不患人之不己知，患不知人也。", "孔子", "论语·学而", "zh"),
    ("君子和而不同，小人同而不和。", "孔子", "论语·子路", "zh"),
    ("岁寒，然后知松柏之后凋也。", "孔子", "论语·子罕", "zh"),
    ("工欲善其事，必先利其器。", "孔子", "论语·卫灵公", "zh"),
    ("人无远虑，必有近忧。", "孔子", "论语·卫灵公", "zh"),
    ("天行健，君子以自强不息。", "《周易》", "周易·乾卦", "zh"),
    ("地势坤，君子以厚德载物。", "《周易》", "周易·坤卦", "zh"),
    ("穷则变，变则通，通则久。", "《周易》", "周易·系辞下", "zh"),
    ("上善若水，水善利万物而不争。", "老子", "道德经·第八章", "zh"),
    ("知人者智，自知者明。", "老子", "道德经·第三十三章", "zh"),
    ("胜人者有力，自胜者强。", "老子", "道德经·第三十三章", "zh"),
    ("大方无隅，大器晚成，大音希声，大象无形。", "老子", "道德经·第四十一章", "zh"),
    ("千里之行，始于足下。", "老子", "道德经·第六十四章", "zh"),
    ("祸兮福之所倚，福兮祸之所伏。", "老子", "道德经·第五十八章", "zh"),
    ("知足不辱，知止不殆。", "老子", "道德经·第四十四章", "zh"),
    ("吾日三省吾身。", "曾子", "论语·学而", "zh"),
    ("富贵不能淫，贫贱不能移，威武不能屈。", "孟子", "孟子·滕文公下", "zh"),
    ("生于忧患，死于安乐。", "孟子", "孟子·告子下", "zh"),
    ("尽信书，则不如无书。", "孟子", "孟子·尽心下", "zh"),
    ("民为贵，社稷次之，君为轻。", "孟子", "孟子·尽心下", "zh"),
    ("天时不如地利，地利不如人和。", "孟子", "孟子·公孙丑下", "zh"),
    ("青，取之于蓝，而青于蓝。", "荀子", "荀子·劝学", "zh"),
    ("不积跬步，无以至千里。", "荀子", "荀子·劝学", "zh"),
    ("锲而舍之，朽木不折；锲而不舍，金石可镂。", "荀子", "荀子·劝学", "zh"),
    ("路漫漫其修远兮，吾将上下而求索。", "屈原", "离骚", "zh"),
    ("亦余心之所善兮，虽九死其犹未悔。", "屈原", "离骚", "zh"),
    ("举世皆浊我独清，众人皆醉我独醒。", "屈原", "渔父", "zh"),
    # ---- 史与文 ----
    ("桃李不言，下自成蹊。", "司马迁", "史记·李将军列传", "zh"),
    ("人固有一死，或重于泰山，或轻于鸿毛。", "司马迁", "报任安书", "zh"),
    ("前事不忘，后事之师。", "《战国策》", "战国策·赵策一", "zh"),
    ("亡羊补牢，未为迟也。", "《战国策》", "战国策·楚策四", "zh"),
    ("静以修身，俭以养德。", "诸葛亮", "诫子书", "zh"),
    ("非淡泊无以明志，非宁静无以致远。", "诸葛亮", "诫子书", "zh"),
    ("鞠躬尽瘁，死而后已。", "诸葛亮", "后出师表", "zh"),
    ("老骥伏枥，志在千里。", "曹操", "龟虽寿", "zh"),
    ("烈士暮年，壮心不已。", "曹操", "龟虽寿", "zh"),
    ("丈夫志四海，万里犹比邻。", "曹植", "赠白马王彪", "zh"),
    ("采菊东篱下，悠然见南山。", "陶渊明", "饮酒·其五", "zh"),
    ("盛年不重来，一日难再晨。", "陶渊明", "杂诗", "zh"),
    ("不为五斗米折腰。", "陶渊明", "晋书·陶潜传", "zh"),
    ("奇文共欣赏，疑义相与析。", "陶渊明", "移居", "zh"),
    ("海内存知己，天涯若比邻。", "王勃", "送杜少府之任蜀州", "zh"),
    ("落霞与孤鹜齐飞，秋水共长天一色。", "王勃", "滕王阁序", "zh"),
    ("老当益壮，宁移白首之心。", "王勃", "滕王阁序", "zh"),
    ("欲穷千里目，更上一层楼。", "王之涣", "登鹳雀楼", "zh"),
    ("大漠孤烟直，长河落日圆。", "王维", "使至塞上", "zh"),
    ("行到水穷处，坐看云起时。", "王维", "终南别业", "zh"),
    ("长风破浪会有时，直挂云帆济沧海。", "李白", "行路难", "zh"),
    ("天生我材必有用，千金散尽还复来。", "李白", "将进酒", "zh"),
    ("安能摧眉折腰事权贵，使我不得开心颜。", "李白", "梦游天姥吟留别", "zh"),
    ("仰天大笑出门去，我辈岂是蓬蒿人。", "李白", "南陵别儿童入京", "zh"),
    ("举杯邀明月，对影成三人。", "李白", "月下独酌", "zh"),
    ("会当凌绝顶，一览众山小。", "杜甫", "望岳", "zh"),
    ("安得广厦千万间，大庇天下寒士俱欢颜。", "杜甫", "茅屋为秋风所破歌", "zh"),
    ("读书破万卷，下笔如有神。", "杜甫", "奉赠韦左丞丈二十二韵", "zh"),
    ("烽火连三月，家书抵万金。", "杜甫", "春望", "zh"),
    ("莫愁前路无知己，天下谁人不识君。", "高适", "别董大", "zh"),
    ("春风得意马蹄疾，一日看尽长安花。", "孟郊", "登科后", "zh"),
    ("谁言寸草心，报得三春晖。", "孟郊", "游子吟", "zh"),
    ("千山鸟飞绝，万径人踪灭。", "柳宗元", "江雪", "zh"),
    ("业精于勤，荒于嬉；行成于思，毁于随。", "韩愈", "进学解", "zh"),
    ("千里马常有，而伯乐不常有。", "韩愈", "马说", "zh"),
    ("书山有路勤为径，学海无涯苦作舟。", "韩愈", "古今贤文", "zh"),
    ("沉舟侧畔千帆过，病树前头万木春。", "刘禹锡", "酬乐天扬州初逢席上见赠", "zh"),
    ("千淘万漉虽辛苦，吹尽狂沙始到金。", "刘禹锡", "浪淘沙", "zh"),
    ("野火烧不尽，春风吹又生。", "白居易", "赋得古原草送别", "zh"),
    ("同是天涯沦落人，相逢何必曾相识。", "白居易", "琵琶行", "zh"),
    ("文章合为时而著，歌诗合为事而作。", "白居易", "与元九书", "zh"),
    ("曾经沧海难为水，除却巫山不是云。", "元稹", "离思", "zh"),
    ("春蚕到死丝方尽，蜡炬成灰泪始干。", "李商隐", "无题", "zh"),
    ("身无彩凤双飞翼，心有灵犀一点通。", "李商隐", "无题", "zh"),
    ("此情可待成追忆，只是当时已惘然。", "李商隐", "锦瑟", "zh"),
    ("夕阳无限好，只是近黄昏。", "李商隐", "乐游原", "zh"),
    ("先天下之忧而忧，后天下之乐而乐。", "范仲淹", "岳阳楼记", "zh"),
    ("不以物喜，不以己悲。", "范仲淹", "岳阳楼记", "zh"),
    ("醉翁之意不在酒，在乎山水之间也。", "欧阳修", "醉翁亭记", "zh"),
    ("忧劳可以兴国，逸豫可以亡身。", "欧阳修", "新五代史·伶官传序", "zh"),
    ("出淤泥而不染，濯清涟而不妖。", "周敦颐", "爱莲说", "zh"),
    ("大江东去，浪淘尽，千古风流人物。", "苏轼", "念奴娇·赤壁怀古", "zh"),
    ("人有悲欢离合，月有阴晴圆缺，此事古难全。", "苏轼", "水调歌头", "zh"),
    ("但愿人长久，千里共婵娟。", "苏轼", "水调歌头", "zh"),
    ("此心安处是吾乡。", "苏轼", "定风波", "zh"),
    ("回首向来萧瑟处，归去，也无风雨也无晴。", "苏轼", "定风波", "zh"),
    ("人生如逆旅，我亦是行人。", "苏轼", "临江仙", "zh"),
    ("不识庐山真面目，只缘身在此山中。", "苏轼", "题西林壁", "zh"),
    ("博观而约取，厚积而薄发。", "苏轼", "稼说送张琥", "zh"),
    ("古之立大事者，不惟有超世之才，亦必有坚忍不拔之志。", "苏轼", "晁错论", "zh"),
    ("竹杖芒鞋轻胜马，谁怕？一蓑烟雨任平生。", "苏轼", "定风波", "zh"),
    ("莫听穿林打叶声，何妨吟啸且徐行。", "苏轼", "定风波", "zh"),
    ("位卑未敢忘忧国。", "陆游", "病起书怀", "zh"),
    ("纸上得来终觉浅，绝知此事要躬行。", "陆游", "冬夜读书示子聿", "zh"),
    ("山重水复疑无路，柳暗花明又一村。", "陆游", "游山西村", "zh"),
    ("王师北定中原日，家祭无忘告乃翁。", "陆游", "示儿", "zh"),
    ("众里寻他千百度，蓦然回首，那人却在灯火阑珊处。", "辛弃疾",
     "青玉案·元夕", "zh"),
    ("醉里挑灯看剑，梦回吹角连营。", "辛弃疾", "破阵子", "zh"),
    ("了却君王天下事，赢得生前身后名。", "辛弃疾", "破阵子", "zh"),
    ("问渠那得清如许，为有源头活水来。", "朱熹", "观书有感", "zh"),
    ("旧书不厌百回读，熟读深思子自知。", "苏轼", "送安惇秀才失解西归", "zh"),
    ("人生自古谁无死，留取丹心照汗青。", "文天祥", "过零丁洋", "zh"),
    ("粉骨碎身浑不怕，要留清白在人间。", "于谦", "石灰吟", "zh"),
    ("千锤万凿出深山，烈火焚烧若等闲。", "于谦", "石灰吟", "zh"),
    ("风声雨声读书声，声声入耳；家事国事天下事，事事关心。",
     "顾宪成", "东林书院对联", "zh"),
    ("天下兴亡，匹夫有责。", "顾炎武", "日知录", "zh"),
    ("海纳百川，有容乃大；壁立千仞，无欲则刚。", "林则徐", "自题联", "zh"),
    ("苟利国家生死以，岂因祸福避趋之。", "林则徐", "赴戍登程口占示家人", "zh"),
    ("落红不是无情物，化作春泥更护花。", "龚自珍", "己亥杂诗", "zh"),
    ("我劝天公重抖擞，不拘一格降人才。", "龚自珍", "己亥杂诗", "zh"),
    ("宝剑锋从磨砺出，梅花香自苦寒来。", "《警世贤文》", "警世贤文", "zh"),
    ("书到用时方恨少，事非经过不知难。", "《警世贤文》", "警世贤文", "zh"),
    # ---- 近现代 ----
    ("横眉冷对千夫指，俯首甘为孺子牛。", "鲁迅", "自嘲", "zh"),
    ("其实地上本没有路，走的人多了，也便成了路。", "鲁迅", "故乡", "zh"),
    ("真的猛士，敢于直面惨淡的人生。", "鲁迅", "记念刘和珍君", "zh"),
    ("不在沉默中爆发，就在沉默中灭亡。", "鲁迅", "记念刘和珍君", "zh"),
    ("愿中国青年都摆脱冷气，只是向上走。", "鲁迅", "热风·随感录四十一", "zh"),
    ("从来如此，便对么？", "鲁迅", "狂人日记", "zh"),
    ("时间就是性命。无端的空耗别人的时间，其实是无异于谋财害命的。",
     "鲁迅", "门外文谈", "zh"),
    ("少年智则国智，少年强则国强。", "梁启超", "少年中国说", "zh"),
    ("人生须知负责任的苦处，才能知道尽责任的乐趣。", "梁启超", "最苦与最乐", "zh"),
    ("独立之精神，自由之思想。", "陈寅恪", "王国维纪念碑碑文", "zh"),
    ("为天地立心，为生民立命，为往圣继绝学，为万世开太平。",
     "张载", "横渠语录", "zh"),
    ("板凳要坐十年冷，文章不写一句空。", "范文澜", "自题", "zh"),
    ("黑夜给了我黑色的眼睛，我却用它寻找光明。", "顾城", "一代人", "zh"),
    ("你站在桥上看风景，看风景的人在楼上看你。", "卞之琳", "断章", "zh"),
    ("从前的日色变得慢，车、马、邮件都慢，一生只够爱一个人。",
     "木心", "从前慢", "zh"),
    ("岁月不饶人，我亦未曾饶过岁月。", "木心", "云雀叫了一整天", "zh"),
    ("我在这世上，只想活得干净、体面、有尊严。", "王小波", "沉默的大多数", "zh"),
    ("人的一切痛苦，本质上都是对自己无能的愤怒。", "王小波", "黄金时代", "zh"),
    ("一个人只拥有此生此世是不够的，他还应该拥有诗意的世界。",
     "王小波", "万寿寺", "zh"),
    ("生活不可能像你想象得那么好，但也不会像你想象得那么糟。",
     "莫泊桑", "一生", "zh"),
    ("世界上只有一种真正的英雄主义，就是认清生活的真相后依然热爱它。",
     "罗曼·罗兰", "米开朗基罗传", "zh"),
    ("所有的大人都曾经是小孩，虽然，只有少数的人记得。",
     "圣埃克苏佩里", "小王子", "zh"),
    ("重要的东西，用眼睛是看不见的。", "圣埃克苏佩里", "小王子", "zh"),
    ("使沙漠显得美丽的，是它在某个地方藏着一口井。",
     "圣埃克苏佩里", "小王子", "zh"),
    ("一个人知道自己为什么而活，就可以忍受任何一种生活。",
     "尼采", "偶像的黄昏", "zh"),
    ("凡是不能杀死我的，终将使我更强大。", "尼采", "偶像的黄昏", "zh"),
    ("我们都在阴沟里，但仍有人仰望星空。", "王尔德", "温德米尔夫人的扇子", "zh"),
    ("爱自己是终身浪漫的开始。", "王尔德", "理想丈夫", "zh"),
    ("做你自己，因为别人都有人做了。", "王尔德", "名言", "zh"),
    ("未经审视的人生不值得过。", "苏格拉底", "申辩篇", "zh"),
    ("所谓自由，不是随心所欲，而是自我主宰。", "康德", "实践理性批判", "zh"),
    ("人生就是一连串的选择，你选择什么，就成为什么。",
     "萨特", "存在主义是一种人道主义", "zh"),
    ("存在先于本质。", "萨特", "存在与虚无", "zh"),
    ("人是被判定为自由的。", "萨特", "存在与虚无", "zh"),
    ("我们受苦，更多是因为想象，而不是因为现实。",
     "塞内加", "致卢西利乌斯书信", "zh"),
    ("并非我们拥有的时间太短，而是我们浪费得太多。",
     "塞内加", "论生命之短暂", "zh"),
    ("你拥有对自己心灵的支配权，而非外部事件。",
     "马可·奥勒留", "沉思录", "zh"),
    ("不要再争论一个好人应该是什么样，去做一个好人。",
     "马可·奥勒留", "沉思录", "zh"),
    ("人能弘道，非道弘人。", "孔子", "论语·卫灵公", "zh"),
    ("人生忽如寄，莫辜负茶、汤和好天气。", "汪曾祺", "人间草木", "zh"),
    ("四方食事，不过一碗人间烟火。", "汪曾祺", "四方食事", "zh"),
    ("很多东西，不是因为美好才坚持，而是因为坚持才美好。", "汪曾祺", "人间草木", "zh"),
    ("你要做的，是把自己活成一支队伍。", "刘瑜", "送你一颗子弹", "zh"),
    ("一个人应该活得是自己并且干净。", "顾城", "顾城诗全集", "zh"),
    ("我们一路奋战，不是为了改变世界，而是为了不让世界改变我们。",
     "《岁月神偷》", "电影台词", "zh"),
    ("愿有岁月可回首，且以深情共白头。", "佚名", "网络流传", "zh"),
    ("热爱可抵岁月漫长。", "佚名", "网络流传", "zh"),
    ("生活的理想，就是为了理想的生活。", "张闻天", "生活的理想", "zh"),
    ("一个人可以被毁灭，但不能被打败。", "海明威", "老人与海", "zh"),
    ("这个世界如此美好，值得人们为它奋斗。", "海明威", "丧钟为谁而鸣", "zh"),
    ("如果你年轻时住在巴黎，巴黎就会跟着你一辈子。", "海明威", "流动的盛宴", "zh"),
    ("任何人都是一个谜，哪怕是最亲近的人。", "马尔克斯", "百年孤独", "zh"),
    ("生命中真正重要的不是你遭遇了什么，而是你记住了什么。",
     "马尔克斯", "活着为了讲述", "zh"),
    ("人不是为了失败而生的。", "海明威", "老人与海", "zh"),
    ("这世上只有一种成功，就是能够用自己喜欢的方式度过一生。",
     "毛姆", "月亮与六便士", "zh"),
    ("我用尽了全力，过着平凡的一生。", "毛姆", "月亮与六便士", "zh"),
    ("满地都是六便士，他却抬头看见了月亮。", "毛姆", "月亮与六便士", "zh"),
    ("一个人如果失去耐心，他就失去了灵魂。", "卡夫卡", "箴言录", "zh"),
    ("目标虽有，却无路可循；我们称之为路的，无非是踌躇。",
     "卡夫卡", "箴言录", "zh"),
    ("真正的光明绝不是永没有黑暗的时间，只是永不被黑暗所掩蔽罢了。",
     "罗曼·罗兰", "约翰·克利斯朵夫", "zh"),
    ("认识你自己。", "德尔斐神庙", "阿波罗神庙铭文", "zh"),
    ("一切皆流，无物常驻。", "赫拉克利特", "残篇", "zh"),
    ("人不能两次踏进同一条河流。", "赫拉克利特", "残篇", "zh"),
    ("我思故我在。", "笛卡尔", "第一哲学沉思集", "zh"),
    ("人生而自由，却无往不在枷锁之中。", "卢梭", "社会契约论", "zh"),
    ("幸福不是一件现成的东西，它来自你自己的行动。", "达赖喇嘛", "名言", "zh"),
    ("要么庸俗，要么孤独。", "叔本华", "人生的智慧", "zh"),
    ("一个人只有在独处时才能成为自己。", "叔本华", "人生的智慧", "zh"),
    ("时间是最宝贵的财富，因为它一去不返。", "塞内加", "论生命之短暂", "zh"),
    ("教育的目的是让人学会提问，而不是给出答案。",
     "苏格拉底", "对话录概述", "zh"),
    ("优秀是一种习惯。", "亚里士多德", "尼各马可伦理学", "zh"),
    ("幸福是灵魂合于德性的活动。", "亚里士多德", "尼各马可伦理学", "zh"),
    ("求知是人类的本性。", "亚里士多德", "形而上学", "zh"),
    ("我们无法选择自己的出身，但可以选择成为什么样的人。", "佚名", "网络流传", "zh"),
    ("不要因为走得太远，忘了我们为什么出发。", "纪伯伦", "先知", "zh"),
    ("你的孩子不是你的孩子，他们是生命对于自身的渴望。",
     "纪伯伦", "先知", "zh"),
    ("你要按你所想的去生活，否则你迟早会按你生活的去想。",
     "爱默生", "随笔集", "zh"),
    ("信心是灵魂的防腐剂。", "爱默生", "随笔集", "zh"),
    ("重要的不是治愈，而是带着病痛活下去。", "加缪", "西西弗神话", "zh"),
    ("在冬天的深处，我终于明白，我心中有一个不可战胜的夏天。",
     "加缪", "夏天", "zh"),
    ("我们必须想象西西弗是幸福的。", "加缪", "西西弗神话", "zh"),
    ("所谓生活的意义，就是你赋予它的意义。", "加缪", "西西弗神话", "zh"),
    ("真正严肃的哲学问题只有一个，那就是自杀。", "加缪", "西西弗神话", "zh"),
    ("人必须拥有自己的太阳。", "尼采", "查拉图斯特拉如是说", "zh"),
    ("每一个不曾起舞的日子，都是对生命的辜负。",
     "尼采", "查拉图斯特拉如是说", "zh"),
    ("当你凝视深渊时，深渊也在凝视着你。", "尼采", "善恶的彼岸", "zh"),
    ("白昼之光，岂知夜色之深。", "尼采", "查拉图斯特拉如是说", "zh"),
    ("一切美好的事物都是曲折地接近自己的目标。", "尼采", "快乐的知识", "zh"),
    ("人生最难的智慧，是学会放弃。", "林语堂", "生活的艺术", "zh"),
    ("生活的智慧在于逐渐澄清滤除那些不重要的杂质。", "林语堂", "生活的艺术", "zh"),
    ("读书可以让人变得有趣。", "林语堂", "生活的艺术", "zh"),
]

QUOTES_EN = [
    ("Not all those who wander are lost.", "J.R.R. Tolkien",
     "The Fellowship of the Ring", "en"),
    ("We are all in the gutter, but some of us are looking at the stars.",
     "Oscar Wilde", "Lady Windermere's Fan", "en"),
    ("To live is the rarest thing in the world. Most people exist, that is all.",
     "Oscar Wilde", "The Soul of Man Under Socialism", "en"),
    ("Be yourself; everyone else is already taken.", "Oscar Wilde",
     "attributed", "en"),
    ("The only way out is through.", "Robert Frost", "A Servant to Servants", "en"),
    ("In three words I can sum up everything I've learned about life: "
     "it goes on.", "Robert Frost", "attributed", "en"),
    ("I took the one less traveled by, and that has made all the difference.",
     "Robert Frost", "The Road Not Taken", "en"),
    ("Stay hungry, stay foolish.", "Steve Jobs",
     "Stanford Commencement, 2005", "en"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci",
     "attributed", "en"),
    ("What we know is a drop, what we don't know is an ocean.",
     "Isaac Newton", "attributed", "en"),
    ("If I have seen further, it is by standing on the shoulders of giants.",
     "Isaac Newton", "letter to Robert Hooke, 1675", "en"),
    ("The unexamined life is not worth living.", "Socrates", "Apology", "en"),
    ("I know that I know nothing.", "Socrates", "attributed", "en"),
    ("Knowing yourself is the beginning of all wisdom.",
     "Aristotle", "attributed", "en"),
    ("We are what we repeatedly do. Excellence, then, is not an act, "
     "but a habit.", "Will Durant", "The Story of Philosophy", "en"),
    ("Happiness depends upon ourselves.", "Aristotle",
     "Nicomachean Ethics", "en"),
    ("We suffer more often in imagination than in reality.",
     "Seneca", "Letters to Lucilius", "en"),
    ("It is not that we have a short time to live, "
     "but that we waste a lot of it.", "Seneca", "On the Shortness of Life", "en"),
    ("Luck is what happens when preparation meets opportunity.",
     "Seneca", "attributed", "en"),
    ("You have power over your mind — not outside events. "
     "Realize this, and you will find strength.", "Marcus Aurelius",
     "Meditations", "en"),
    ("Waste no more time arguing what a good man should be. Be one.",
     "Marcus Aurelius", "Meditations", "en"),
    ("Very little is needed to make a happy life; "
     "it is all within yourself, in your way of thinking.",
     "Marcus Aurelius", "Meditations", "en"),
    ("The impediment to action advances action. "
     "What stands in the way becomes the way.", "Marcus Aurelius",
     "Meditations", "en"),
    ("He who has a why to live can bear almost any how.",
     "Friedrich Nietzsche", "Twilight of the Idols", "en"),
    ("That which does not kill us makes us stronger.",
     "Friedrich Nietzsche", "Twilight of the Idols", "en"),
    ("And those who were seen dancing were thought to be insane "
     "by those who could not hear the music.", "Friedrich Nietzsche",
     "attributed", "en"),
    ("Life can only be understood backwards; but it must be lived forwards.",
     "Søren Kierkegaard", "Journals", "en"),
    ("Man is condemned to be free.", "Jean-Paul Sartre",
     "Being and Nothingness", "en"),
    ("Hell is other people.", "Jean-Paul Sartre", "No Exit", "en"),
    ("The mass of men lead lives of quiet desperation.",
     "Henry David Thoreau", "Walden", "en"),
    ("Go confidently in the direction of your dreams. "
     "Live the life you have imagined.", "Henry David Thoreau", "Walden", "en"),
    ("It does not matter how slowly you go so long as you do not stop.",
     "Confucius", "Analects", "en"),
    ("The journey of a thousand miles begins with a single step.",
     "Laozi", "Tao Te Ching", "en"),
    ("A room without books is like a body without a soul.",
     "Cicero", "attributed", "en"),
    ("Genius is one percent inspiration, ninety-nine percent perspiration.",
     "Thomas Edison", "attributed", "en"),
    ("I have not failed. I've just found 10,000 ways that won't work.",
     "Thomas Edison", "attributed", "en"),
    ("Imagination is more important than knowledge.",
     "Albert Einstein", "attributed", "en"),
    ("The important thing is not to stop questioning.",
     "Albert Einstein", "attributed", "en"),
    ("Try not to become a man of success, "
     "but rather try to become a man of value.", "Albert Einstein",
     "attributed", "en"),
    ("Be the change that you wish to see in the world.",
     "Mahatma Gandhi", "attributed", "en"),
    ("The only thing we have to fear is fear itself.",
     "Franklin D. Roosevelt", "First Inaugural Address, 1933", "en"),
    ("Do not go gentle into that good night.", "Dylan Thomas",
     "Do not go gentle into that good night", "en"),
    ("Hope is the thing with feathers that perches in the soul.",
     "Emily Dickinson", "Hope is the thing with feathers", "en"),
    ("So we beat on, boats against the current, "
     "borne back ceaselessly into the past.", "F. Scott Fitzgerald",
     "The Great Gatsby", "en"),
    ("All happy families are alike; each unhappy family "
     "is unhappy in its own way.", "Leo Tolstoy", "Anna Karenina", "en"),
    ("The mystery of human existence lies not in just staying alive, "
     "but in finding something to live for.", "Fyodor Dostoevsky",
     "The Brothers Karamazov", "en"),
    ("There is no greater agony than bearing an untold story inside you.",
     "Maya Angelou", "I Know Why the Caged Bird Sings", "en"),
    ("You may not control all the events that happen to you, "
     "but you can decide not to be reduced by them.", "Maya Angelou",
     "Letter to My Daughter", "en"),
    ("Happiness is not something ready made. "
     "It comes from your own actions.", "Dalai Lama", "attributed", "en"),
    ("Time is the most valuable thing a man can spend.",
     "Theophrastus", "attributed", "en"),
    ("The two most powerful warriors are patience and time.",
     "Leo Tolstoy", "War and Peace", "en"),
    ("Man is the only creature who refuses to be what he is.",
     "Albert Camus", "The Rebel", "en"),
    ("In the depth of winter, I finally learned that within me "
     "there lay an invincible summer.", "Albert Camus", "Return to Tipasa", "en"),
    ("Should I kill myself, or have a cup of coffee?",
     "Albert Camus", "attributed", "en"),
    ("You cannot swim for new horizons until you have courage "
     "to lose sight of the shore.", "William Faulkner", "attributed", "en"),
    ("The past is never dead. It's not even past.", "William Faulkner",
     "Requiem for a Nun", "en"),
    ("There is no friend as loyal as a book.", "Ernest Hemingway",
     "attributed", "en"),
    ("A man can be destroyed but not defeated.", "Ernest Hemingway",
     "The Old Man and the Sea", "en"),
    ("The world breaks everyone, and afterward, many are strong "
     "at the broken places.", "Ernest Hemingway", "A Farewell to Arms", "en"),
    ("Nothing is faster than the speed of light, except your mind "
     "when it realizes something.", "Niels Bohr", "attributed", "en"),
    ("An expert is a person who has made all the mistakes that can be made "
     "in a very narrow field.", "Niels Bohr", "attributed", "en"),
    ("Not all readers are leaders, but all leaders are readers.",
     "Harry S. Truman", "attributed", "en"),
    ("The best way to predict the future is to invent it.",
     "Alan Kay", "attributed", "en"),
    ("Simple things should be simple, complex things should be possible.",
     "Alan Kay", "attributed", "en"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds", "mailing list, 2000", "en"),
    ("Programs must be written for people to read, "
     "and only incidentally for machines to execute.",
     "Harold Abelson", "Structure and Interpretation of Computer Programs", "en"),
    ("Premature optimization is the root of all evil.", "Donald Knuth",
     "The Art of Computer Programming", "en"),
    ("Any sufficiently advanced technology is indistinguishable from magic.",
     "Arthur C. Clarke", "Profiles of the Future", "en"),
    ("The opposite of a fact is falsehood, but the opposite of "
     "one profound truth may very well be another profound truth.",
     "Niels Bohr", "attributed", "en"),
    ("A ship in harbor is safe, but that is not what ships are built for.",
     "John A. Shedd", "Salt from My Attic", "en"),
    ("You miss 100 percent of the shots you don't take.",
     "Wayne Gretzky", "attributed", "en"),
    ("It always seems impossible until it's done.",
     "Nelson Mandela", "attributed", "en"),
    ("Education is the most powerful weapon which you can use "
     "to change the world.", "Nelson Mandela", "attributed", "en"),
    ("The man who moves a mountain begins by carrying away small stones.",
     "Confucius", "attributed", "en"),
    ("When I let go of what I am, I become what I might be.",
     "Laozi", "Tao Te Ching", "en"),
    ("Nature does not hurry, yet everything is accomplished.",
     "Laozi", "Tao Te Ching", "en"),
    ("He who knows others is wise; he who knows himself is enlightened.",
     "Laozi", "Tao Te Ching", "en"),
    ("Do not fear going forward slowly; fear only to stand still.",
     "Chinese proverb", "proverb", "en"),
    ("The best time to plant a tree was twenty years ago. "
     "The second best time is now.", "Chinese proverb", "proverb", "en"),
    ("Fall seven times, stand up eight.", "Japanese proverb", "proverb", "en"),
    ("Vision without action is a daydream. Action without vision is a nightmare.",
     "Japanese proverb", "proverb", "en"),
    ("A smooth sea never made a skilled sailor.", "English proverb",
     "proverb", "en"),
    ("The darkest hour is just before the dawn.", "English proverb",
     "proverb", "en"),
    ("Where there is a will, there is a way.", "English proverb",
     "proverb", "en"),
    ("What you do every day matters more than what you do once in a while.",
     "Gretchen Rubin", "The Happiness Project", "en"),
    ("We become what we think about.", "Earl Nightingale",
     "The Strangest Secret", "en"),
    ("You are never too old to set another goal "
     "or to dream a new dream.", "C.S. Lewis", "attributed", "en"),
    ("Hardships often prepare ordinary people for an extraordinary destiny.",
     "C.S. Lewis", "attributed", "en"),
    ("Friendship is born at that moment when one person says to another, "
     "'What! You too? I thought I was the only one.'", "C.S. Lewis",
     "The Four Loves", "en"),
    ("There are far better things ahead than any we leave behind.",
     "C.S. Lewis", "attributed", "en"),
    ("Courage is not the absence of fear, but the triumph over it.",
     "Nelson Mandela", "Long Walk to Freedom", "en"),
    ("A reader lives a thousand lives before he dies. "
     "The man who never reads lives only one.", "George R.R. Martin",
     "A Dance with Dragons", "en"),
    ("It is our choices that show what we truly are, "
     "far more than our abilities.", "J.K. Rowling",
     "Harry Potter and the Chamber of Secrets", "en"),
    ("Happiness can be found even in the darkest of times, "
     "if one only remembers to turn on the light.", "J.K. Rowling",
     "Harry Potter and the Prisoner of Azkaban", "en"),
    ("Of course it is happening inside your head, Harry, "
     "but why on earth should that mean that it is not real?",
     "J.K. Rowling", "Harry Potter and the Deathly Hallows", "en"),
    ("Stars can't shine without darkness.", "D.H. Sidebottom",
     "attributed", "en"),
    ("You do not have to be good. You do not have to walk on your knees "
     "for a hundred miles through the desert, repenting.",
     "Mary Oliver", "Wild Geese", "en"),
    ("Tell me, what is it you plan to do with your one wild "
     "and precious life?", "Mary Oliver", "The Summer Day", "en"),
    ("Somewhere, something incredible is waiting to be known.",
     "Carl Sagan", "attributed", "en"),
    ("We are a way for the cosmos to know itself.", "Carl Sagan", "Cosmos", "en"),
    ("Extraordinary claims require extraordinary evidence.",
     "Carl Sagan", "Cosmos", "en"),
    ("The cosmos is within us. We are made of star-stuff.",
     "Carl Sagan", "Cosmos", "en"),
    ("Look again at that dot. That's here. That's home. That's us.",
     "Carl Sagan", "Pale Blue Dot", "en"),
    ("To err is human, to forgive divine.", "Alexander Pope",
     "An Essay on Criticism", "en"),
    ("No man is an island, entire of itself.", "John Donne",
     "Meditation XVII", "en"),
    ("Knowledge is power.", "Francis Bacon", "Meditationes Sacrae", "en"),
    ("Reading maketh a full man; conference a ready man; "
     "and writing an exact man.", "Francis Bacon", "Of Studies", "en"),
    ("Some books are to be tasted, others to be swallowed, "
     "and some few to be chewed and digested.", "Francis Bacon",
     "Of Studies", "en"),
    ("Whatever the mind can conceive and believe, it can achieve.",
     "Napoleon Hill", "Think and Grow Rich", "en"),
    ("The only thing standing between you and your goal is the story "
     "you keep telling yourself as to why you can't achieve it.",
     "Jordan Belfort", "attributed", "en"),
    ("Success is not final, failure is not fatal: "
     "it is the courage to continue that counts.", "Winston Churchill",
     "attributed", "en"),
    ("If you're going through hell, keep going.", "Winston Churchill",
     "attributed", "en"),
    ("History will be kind to me for I intend to write it.",
     "Winston Churchill", "attributed", "en"),
    ("To improve is to change; to be perfect is to change often.",
     "Winston Churchill", "attributed", "en"),
]

ALL = QUOTES_ZH + QUOTES_EN


def _merge(base, extra):
    """合并时按正文去重，先出现的保留（原有的优先于新增的）。"""
    seen = set()
    out = []
    for item in base + extra:
        body = item[0]
        key = body.strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


# 扩充的句子单独放，主文件不至于太长
try:
    import quotes_more
    import quotes_en_more

    QUOTES_ZH = _merge(QUOTES_ZH, quotes_more.MORE_ZH)
    QUOTES_EN = _merge(QUOTES_EN, quotes_en_more.MORE_EN)
    ALL = QUOTES_ZH + QUOTES_EN
except ImportError:  # 没装扩充文件也能跑
    pass


def _pool(lang):
    if lang == "zh":
        return QUOTES_ZH
    if lang == "en":
        return QUOTES_EN
    return ALL


def daily_index(today=None, lang="all"):
    """按日期确定当天那句，同一天刷新不变。

    用 blake2b 而不是 sha256：摘要更分散，再掺进月份和星期，
    避免"相邻的日子落在相邻的句子上"这种看起来不随机的问题。
    """
    today = today or date.today()
    pool = _pool(lang)
    seed = f"{today.isoformat()}|{today.month}|{today.weekday()}|quotes-v2"
    digest = hashlib.blake2b(seed.encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big") % len(pool)


def random_index(lang="all", exclude=None):
    """真随机取一句（「换一句」用）。

    不用顺序 +1，那样连点几次就是照着列表往下读，看不出随机。
    """
    pool = _pool(lang)
    if not pool:
        return 0
    if len(pool) == 1:
        return 0
    for _ in range(8):
        idx = secrets.randbelow(len(pool))
        if idx != exclude:
            return idx
    return secrets.randbelow(len(pool))


def get(offset=0, today=None, lang="all"):
    """取一句。

    offset 为 0 时是「今天这句」（整天不变）；
    offset 非 0 时当作「换一句」，返回真随机的一句。
    """
    pool = _pool(lang)
    if not pool:
        return {"body": "", "author": "", "source": "", "lang": "zh",
                "index": 0, "total": 0}
    if offset:
        idx = random_index(lang)
    else:
        idx = daily_index(today, lang)
    body, author, source, code = pool[idx]
    return {"body": body, "author": author, "source": source,
            "lang": code, "index": idx, "total": len(pool)}


def by_index(index, lang="all"):
    pool = _pool(lang)
    if not pool:
        return get(0, lang=lang)
    index %= len(pool)
    body, author, source, code = pool[index]
    return {"body": body, "author": author, "source": source,
            "lang": code, "index": index, "total": len(pool)}


if __name__ == "__main__":
    print(f"中文 {len(QUOTES_ZH)} 句，英文 {len(QUOTES_EN)} 句，共 {len(ALL)} 句")

    # 自检：重复、空字段、长度
    bodies = [q[0] for q in ALL]
    dupes = {b for b in bodies if bodies.count(b) > 1}
    print("重复句子:", dupes if dupes else "无")
    empty = [q for q in ALL if not all(q)]
    print("空字段:", len(empty))
    longest = max(len(q[0]) for q in ALL)
    print("最长一句:", longest, "字符")

    print()
    for offset in range(4):
        q = get(offset)
        tag = "中" if q["lang"] == "zh" else "EN"
        src = f"《{q['source']}》" if q["lang"] == "zh" else q["source"]
        print(f"[{tag}] {q['body']}")
        print(f"      —— {q['author']} {src} (#{q['index']}/{q['total']})")
