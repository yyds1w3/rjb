var ajaxUrl = '/queryList';//请求分页地址
var pageSize = 25;//每页条数
var siteDataname = "国家疾病预防控制局";
//稿件信息全写、简写字段
var articleTrans = {
    title: 'aT',//标题全写
    summary: 'aS',//摘要;视频简介全写
    keywords: 'aKey',//关键词全写
    tags: 'aTag',//标签全写
    images: 'aI',//图片集合;展示封面全写
    articleFiles: 'aAf',//附件id集合全写
    classify: 'aC',//稿件类型（0：图文，1：超链接，2;附件，3：视频，4：动态，5：直播，6：图集）全写
    urls: 'aU',//发布地址集合全写
    publishId: 'aPi',//发布人id全写
    publishName: 'aPn',//发布人名称全写
    publishTime: 'aPt',//发布时间全写
    pubDate: 'aPd',//渠道推送过来的发布时间全写
    redirectUrl: 'aRu',//重定向地址全写
    archiveStatus: 'aAs',//归档状态(1 :  归档 0 : 未归档)全写
    topStatus: 'aTs',//置顶状态 0 未置顶 (1-10 为置顶值)全写
    relation: 'aR',//是否设置了关联稿件(0:未关联 1:关联)全写
	source:'aLy',//来源
};

//栏目信息全写、简写字段
var channelTrans = {
    name: 'cN',//栏目名称全写
    code: 'cC',//栏目代号全写
    redirectLink: 'cRl',//栏目重定向链接全写
    classification: 'cCla',//栏目类别全写
    channelType: 'cCt',//栏目类型全写
    tags: 'cTag',//栏目标签全写
    fileFlag: 'cFf',//栏目归档标记(是否归档：0-未归档、1-已归档)全写
    urls: 'cU',//栏目概览页发布地址全写
    releaseTime: 'cRt',//栏目发布时间全写
    childCount: 'cCc',//子级栏目数量全写
};

//关联稿件信息全写、简写字段
var relationTrans = {
    title: 'rT',//关联稿件标题全写
    urls: 'rU',//关联稿件发布地址全写
    sortNum: 'rSn',//关联稿件id全写
};

//站点数据信息全写、简写字段
var websiteTrans = {
    name: 'wN',//网站名称全写
    urls: 'rU',//网站发布路径全写
    path: 'wP',//关联稿件id全写
    deptName: 'wDpN',//机构名称全写
    domainName: 'wDn',//网站域名全写
    faviconPath: 'wFp',//图标地址全写
    code: 'wC',//网站代号全写
    siteIdCode: 'wSc',//网站标识码全写
    contactInfo: 'wCi',//联系电话全写
    icpFiling: 'wIcp',//ICP备案全写
    publicNetworkSecurity: 'wPns',//公网安备全写
    watermarkUrl: 'wWu',//归档水印url全写
};
//过滤html标签
  var filterHTMLTag = function(str) {
        return str.replace(/<[^>]+>/g,"");
    };
var transformTool = function (transformObj, data) {
    var transformData = data;
    if (transformObj) {
        for (var key in transformObj) {
            var value = transformObj[key];
            if (transformData[key] === undefined) {
                transformData[key] = transformData[value];
            } else if (transformData[value] === undefined) {
                transformData[value] = transformData[key];
            }
        }
    }
    return transformData
};

//获取导航菜单栏目列表
var getNavbarInfo = function (data, dom) {
    //data网站数据 dom要添加的dom元素
    //示例：
    //var siteMsg = <ucap:websiteTag></ucap:websiteTag>;
    //getNavbarInfo(siteMsg, '.nav');
	//console.log(data)
    var navStr = '<li><a href="/jbkzzx/index.html">首页</a></li>';
    var siteData = transformTool(websiteTrans, data);
	//console.log(siteData.name);
	siteDataname = siteData.name;
    if (siteData.children && siteData.children.length) {
        siteData.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
            if (index < 5) {
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
                navStr += '<li class="' + siteItem.cC + '"><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
            }
        });
        $(dom).html(navStr);
    }
};
//头部下拉子栏目
var lxlmlist = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'">'+data.cN+'</a></p><ul class="clearfix">';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(siteItem.cN == "信息速递"||siteItem.cN == "头条新闻"){
					channeStr+='';
				}else{
					if(siteItem.redirectLink!==''){
					channeStr += '<li><a href="' + siteItem.redirectLink + '" target="_blank">' + siteItem.cN + '</a></li>';
					}else if(siteItem.crumbs.length>1){
					channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
					}
				}
        });
		channeStr+='</ul>';
        $(listDom).html(channeStr);
    }
};
//网站地图-新闻咨询子栏目 去掉’'信息速递'
var xwzxlmlist = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'">'+data.cN+'</a></p><ul class="clearfix">';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(siteItem.cN == "信息速递"||siteItem.cN == "头条新闻"){
					channeStr+='';
				}else{
					if(siteItem.redirectLink!==''){
					channeStr += '<li><a href="' + siteItem.redirectLink + '" target="_blank">' + siteItem.cN + '</a></li>';
					}else if(siteItem.crumbs.length>1){
					channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
					}
				}
        });
		channeStr+='</ul>';
        $(listDom).html(channeStr);
    }
};
//互动交流下拉子栏目
var hdjllist = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'">'+data.cN+'</a></p><ul class="clearfix"><li><a href="/jbkzzx/c100044/list/list.html" target="_blank">留言选登</a></li>';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(index>0){
					if(siteItem.redirectLink!==''){
					channeStr += '<li><a href="' + siteItem.redirectLink + '" target="_blank">' + siteItem.cN + '</a></li>';
					}else if(siteItem.crumbs.length>1){
					channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
					}
				}				
        });
		channeStr+='</ul>';
        $(listDom).html(channeStr);
    }
};
//政务公开下拉子栏目
var zwgknavlist = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'" target="_blank">'+data.cN+'</a></p><ul class="zwgkulafter"><li><a href="/jbkzzx/c100025/common/list.html">政府信息公开</a></li>';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(index<4){
					channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
				}else if(index>4&&index<5){
					channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';
				}
                
        });
		//channeStr+='<li><a href="/jbkzzx/c100030/common/list.html" target="_blank">规划计划</a></li></ul>';
        $(listDom).html(channeStr);
    }
};
//政务公开下拉子栏目
var zwgknavlist2 = function (data, listDom) {
    
    var channeStr = '<ul class="zwgkul2">';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
			//console.log(siteItem)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(index>0){
					channeStr += '<li><a href="' + urlsObj.second + '" target="_blank">' + siteItem.cN + '</a></li>';
				}
                
        });
		channeStr+='</ul>';
        $(listDom).append(channeStr);
    }
};
//网站地图-政务公开所有子栏目
var zwgknavlistall = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'">'+data.cN+'</a></p><ul class="clearfix"><li><a href="/jbkzzx/c100025/common/list.html">政府信息公开</a></li>';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
				if(index<8){
					if(siteItem.cN!=='政府信息公开'){
						channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';   
					}					       
				}
									      
        });	
		channeStr+='<li><a href="/jbkzzx/c100030/second/list.html" target="_blank">规划计划</a></li><li><a href="/jbkzzx/c100016/second/list.html" target="_blank">疫情信息</a></li><li><a href="/jbkzzx/c100019/second/list.html" target="_blank">财务信息</a></li><li><a href="/jbkzzx/c100033/second/list.html" target="_blank">建议提案</a></li><li><a href="/jbkzzx/c100034/second/list.html" target="_blank">人事信息</a></li>';
        $(listDom).html(channeStr);
    }
};
//网站地图-专题专栏所有子栏目 +'信息速递'
var ztzlnavlistall = function (data, listDom) {
    	//console.log(data)
		 if (data.cU) {
                    urlsObj1 = JSON.parse(data.cU);
                }
    var channeStr = '<p><a href="'+urlsObj1.common+'">'+data.cN+'</a></p><ul class="clearfix"><li><a href="/jbkzzx/yqxxxw/common/list.html">信息速递</a></li>';
    if (data.children && data.children.length) {
        data.children.forEach(function (item, index) {
            var siteItem = transformTool(channelTrans, item)
                var urlsObj = {};
                if (siteItem.cU) {
                    urlsObj = JSON.parse(siteItem.cU);
                }
						channeStr += '<li><a href="' + urlsObj.common + '" target="_blank">' + siteItem.cN + '</a></li>';   			      
        });	
		channeStr+='</ul>';
        $(listDom).html(channeStr);
    }
};
//添加网站图标ico
var addIco = function (data) {
    //data网站基本信息数据
    //示例：
    //var siteMsg = <ucap:websiteTag></ucap:websiteTag>;
    //addIco(siteMsg);
    if (data) {
        var siteData = transformTool(websiteTrans, data)
        if (siteData.wFp) {
            var link = document.createElement('link');
            link.type = 'image/x-icon';
            link.rel = 'shortcut icon';
            link.href = siteData.wFp;
            document.getElementsByTagName('head')[0].appendChild(link);
        }
    }
};
///添加面包屑导航
var addcrumbs = function (data, breadDom) {
    //data当前栏目数据 listDom添加面包屑的dom元素
    //示例：
    //var channelsTag = <ucap:channelsTag></ucap:channelsTag>;
    //addcrumbs(channelsTag, '.BreadcrumbNav');
    if (data) {
        var channelData = transformTool(channelTrans, data)
        if (channelData.crumbs && channelData.crumbs.length) {
            for (var i = 0; i < channelData.crumbs.length; i++) {
                var crumbItem = channelData.crumbs[i];
                $(breadDom).append('<span> > </span><a href="' + (crumbItem.urls?crumbItem.urls.common:'javascript:void(0);') + '" >' + crumbItem.name + '</a>');
            }
        }
    }
};

//概览页稿件列表
var addArticleList = function (data, listDom, fromType) {
    //data栏目列表数据 channelsTag栏目基本信息 webSiteCode网站code listDom添加列表dom元素 fromType=pagination表示是分页数据
    //示例：
    //var itemObj = <ucap:articleListIncludeTag></ucap:articleListIncludeTag>;
    //addArticleList(itemObj, '.articleList');
    if (data) {
        var articleStr = '';
        $(listDom).html('')
        if (data && data.length) {
            data.forEach(function (item, index) {
                if (index < pageSize) {
                    var itemObj = '';
                    if (fromType && fromType == 'pagination') {
                        itemObj = item.source;
                    } else {
                        itemObj = item;
                    }
                    itemObj = transformTool(articleTrans, itemObj);
                    var urlsObj = itemObj.aU;					
                    if (urlsObj) urlsObj = JSON.parse(urlsObj);
					var articleUrl=itemObj.redirectUrl!==undefined&&itemObj.redirectUrl!==''?itemObj.redirectUrl:urlsObj.common;
                    articleStr = '<li class="clearfix">' +
                        '<span class="circle"></span>' +
                        '<a href="' + (articleUrl?articleUrl:'') + '" target="_blank"><img src="/jbkzzx/images/list/li.png"><p>' + (itemObj.aT).replace(/<[^>]+>|&[^>]+;/g, '') + '<p><span class="time">' + itemObj.aPd.split(' ')[0] + '</span></a>' +
                        '</li>';
                    $(listDom).append(articleStr);
                }
            })
        }
    }
};
//疾病控制标准列表
var addgjList = function (data, listDom, fromType,num) {
    //data栏目列表数据 channelsTag栏目基本信息 webSiteCode网站code listDom添加列表dom元素 fromType=pagination表示是分页数据
    //示例：
    //var itemObj = <ucap:articleListIncludeTag></ucap:articleListIncludeTag>;
    //addArticleList(itemObj, '.articleList');
    if (data) {
        var articleStr = '';
        $(listDom).html('')
        if (data && data.length) {
            data.forEach(function (item, index) {
                if (index < 5) {
                    var itemObj = '';
                    if (fromType && fromType == 'pagination') {
                        itemObj = item.source;
                    } else {
                        itemObj = item;
                    }
                    itemObj = transformTool(articleTrans, itemObj);
                    var urlsObj = itemObj.aU;					
                    if (urlsObj) urlsObj = JSON.parse(urlsObj);
					var articleUrl=itemObj.redirectUrl!==undefined&&itemObj.redirectUrl!==''?itemObj.redirectUrl:urlsObj.common;
				
						 articleStr = '<li class="clearfix">' +
                        '<span class="circle"></span>' +
                        '<a href="' + (articleUrl?articleUrl:'') + '" target="_blank"><img src="/jbkzzx/images/list/li.png"><p>' + (itemObj.aT).replace(/<[^>]+>|&[^>]+;/g, '') + '<p><span class="time">' + itemObj.aPd.split(' ')[0] + '</span></a>' +
                        '</li>';
					
                    $(listDom).append(articleStr);
                }
            })
        }
    }
};
//概览页分页
var getArticlePage = function (channelsTag, webSiteCode, listDom, pageDom) {
    //channelsTag栏目基本信息 webSiteCode网站code listDom添加列表dom元素 pageDom分页dom元素
    //示例：
    //var webSiteCode = "${website.code}";
    //var channelsTag = <ucap:channelsTag></ucap:channelsTag>;
    //getArticlePage(channelsTag, webSiteCode, '.articleList', '.pagination');
    var channelData = transformTool(channelTrans, channelsTag);
    $.ajax({
        url: ajaxUrl,
        method: 'POST',
        data: {
            current: 1,
            pageSize: pageSize,
            webSiteCode: [webSiteCode],
            channelCode: [channelData.cC]
        },
        success: function (res) {
            if (res.data.results && res.data.results.length > 0) {
                var pageCount = res.data.total % pageSize > 0 ? 1 + parseInt(res.data.total / pageSize) : parseInt(res.data.total / pageSize)
                if (pageCount > 1) {
                    $(pageDom).pagination({
                        pageCount: pageCount,
                        coping: true,
                        homePage: '首页',
                        endPage: '末页',
                        prevContent: '上页',
                        nextContent: '下页',
                        callback: function (api) {
                            //console.log(api.getCurrent())
                            articlePageCbk(api.getCurrent(), channelData, webSiteCode, listDom)
                        }
                    });
                }
            }
        },
        error: function (err) {
            console.log(err)
        }
    })
};

// 概览页点击分页调取数据
var articlePageCbk = function (pageNum, channelData, webSiteCode, listDom) {
    $.ajax({
        url: ajaxUrl,
        method: 'POST',
        data: {
            current: pageNum,
            pageSize: pageSize,
            webSiteCode: [webSiteCode],
            channelCode: [channelData.cC]
        },
        success: function (res) {
           // console.log(res)
            if (res.data.results && res.data.results.length > 0) {
                addArticleList(res.data.results, listDom, 'pagination');
            } else {
                alert('列表获取失败')
            }
        },
        error: function (err) {
            console.log(err)
        }
    })
};

//概览页关联稿件
var addRelationArticle = function (data, dom) {
    //data关联稿件数据 listDom添加关联稿件的dom元素
    //示例：
    //var relationArticleTag = <ucap:relationArticleTag></ucap:relationArticleTag> || [];
    //addRelationArticle(relationArticleTag,'.relation-article-box')
    if (data && data.length) {
        var relationData = transformTool(relationTrans, data);
        var relationStr = '';
        relationData.forEach(function (item) {
            var urls = item.rU;
            if (urls) {
                urls = JSON.parse(urls);
            }
            relationStr += '<li><a href="' + urls.common + '" target="_blank">' + item.rT + '</a></li>'
        })
        $(dom).html('<h4>关联稿件</h4><ul>' + relationStr + '</ul>')
    }
}

//添加网站归档信息
var addChannelTag = function (data, websiteData, dom) {
    //data当前栏目数据 websiteData网站基本信息 dom添加归档信息的dom元素
    //示例：
    //var channelsTag = <ucap:channelsTag></ucap:channelsTag>;
    //addChannelTag(channelsTag,'.right-content');
    //var fileFlag = (data?.fileFlag || data?.archiveStatus || '') + ''
	var fileFlag = (data?data.fileFlag:data?data.archiveStatus:'') + ''
    if (fileFlag === '1') {
        var siteData = transformTool(websiteTrans, websiteData)
        $(dom).append('<div class="water-mark"><img src="' + siteData.wWu + '"/></div>')
    }
}
//首页-轮播图/新闻咨询-轮播图-渲染4条
var lbtlist = function (data, webSiteCode, swiperDom) { 
    if (data) {
		//console.log(data)
        var swiperStr = '';
        if (data && data.length) {
            data.forEach(function (item, index) {
                var articleItem = transformTool(articleTrans, item)
                if (index > 4) return
				var urlsObj = {common: 'javascript:void(0)'};
                if (articleItem.aU) urlsObj = JSON.parse(articleItem.aU);
				var imgObj = {};
                if (articleItem.aI && typeof articleItem.aI == 'string' && JSON.parse(articleItem.aI)?JSON.parse(articleItem.aI.length):'') {
                    imgObj = JSON.parse(articleItem.aI)[0];
                } else if (typeof articleItem.aI == 'object' && JSON.parse(articleItem.aI.length)) {
                    imgObj = articleItem.aI[0];
                }
				//console.log(imgObj+"imgObj");
				if(imgObj == ""||imgObj == {}||imgObj == undefined){
					swiperStr += '<li class="swiper-slide">' +
                        '<a href="' + urlsObj.common + '" target="_blank">' +
                        '<img src=""/>' +
                        '<p class="title">' + filterHTMLTag(articleItem.aT) + '</p>' +
                        '</a>' +
                        '</li>';
				}else{
					swiperStr += '<li class="swiper-slide">' +
                        '<a href="' + urlsObj.common + '" target="_blank">' +
                        '<img src="' +imgObj.cover + '"/>' +
                        '<p class="title">' + filterHTMLTag(articleItem.aT) + '</p>' +
                        '</a>' +
                        '</li>';
				}
                    
            });
        }
        $(swiperDom).html(swiperStr);
    }
};


//添加首页栏目信息
var addChannelInfo = function (data, titleDom, linkDom,sjlink) {
    //data栏目基本信息数据 titleDom添加栏目名称的dom元素 linkDom添加栏目链接的dom元素
    //示例：
    //var newsChannelsTag = <ucap:channelsTag code="XWZX"></ucap:channelsTag>;
    //addChannelInfo(newsChannelsTag, ".newsTitle span", ".newsTitle a");
    if (data) {
        var channelData = transformTool(channelTrans, data)
        $(titleDom).html(channelData.cN);
        if (channelData.cU) {
            if ((typeof channelData.cU) == 'string') {
                var newsItemUrls = JSON.parse(channelData.cU);
                $(linkDom).attr('href', newsItemUrls.common);
				$(sjlink).attr('href', newsItemUrls.common);
            } else {
                $(linkDom).attr('href', channelData.cU.common);
            }
        }
    }
};


//只添加栏目链接
var addChannellj = function (data, titleDom) {
    if (data) {
        var channelData = transformTool(channelTrans, data)
        if (channelData.cU) {
            if ((typeof channelData.cU) == 'string') {
                var newsItemUrls = JSON.parse(channelData.cU);
                $(titleDom).attr('href', newsItemUrls.common);
            }
        }
    }
};
//只添加栏目重定向链接
var addRedirectChannellj = function (data, titleDom) {
    if (data) {
        var channelData = transformTool(channelTrans, data)
		//console.log(channelData);
        if (channelData.cRl) {
            if ((typeof channelData.cRl) == 'string') {
                $(titleDom).attr('href', channelData.cRl);
				$(titleDom).attr('target','_blank');
            }
        }
    }
};


//新闻资讯-新闻发布会列表展示-渲染1条  政务公开-党建工作
var xwfbhlist = function (data, listDom) {    
    var xwfbhlistStr = '';
    if (data && data.length) {
        data.forEach(function (item, index) {
            var xwfbhlistItem = transformTool(articleTrans, item);
            var urlsObj = {common: 'javascript:void(0)'};
            if (xwfbhlistItem.aU) {
                urlsObj = JSON.parse(xwfbhlistItem.aU);
            }
			//console.log(xwfbhlistItem);
			if (index > 0) return
			if (xwfbhlistItem.aU) urlsObj = JSON.parse(xwfbhlistItem.aU);
				var imgObj = {};
				if(xwfbhlistItem.aI!==undefined&&xwfbhlistItem.aI!=="[]"){
					if (xwfbhlistItem.aI && typeof xwfbhlistItem.aI == 'string' && JSON.parse(xwfbhlistItem.aI)?xwfbhlistItem.aI.length:'') {
						imgObj = JSON.parse(xwfbhlistItem.aI)[0];
					} else if (typeof xwfbhlistItem.aI == 'object' && xwfbhlistItem.aI.length) {
						imgObj = xwfbhlistItem.aI[0];
					}
				}else{
					imgObj.cover='';
				}
				  xwfbhlistStr += '<a href="' + urlsObj.common + '" target="_blank"><img src="' + imgObj.cover + '"/><h4>' + filterHTMLTag(xwfbhlistItem.aT) + '</h4><p><font>时间：</font>'+xwfbhlistItem.aPd.split('T')[0].substr(0, 10) +'</p></a>'							         
        });
    }
    $(listDom).html(xwfbhlistStr);
};
//关联稿件
 var addAppendixArticle=function (data, dom, callback) {
        //data关联稿件数据 listDom添加关联稿件的dom元素
        //示例：
        // var articleAppendix = ${articleFiles};
        // commonApi.addAppendixArticle(articleAppendix, '.article-appendix .infolist');
        // console.log('appendixData',data);
        if (!data) return;
        if (typeof data === 'string') {
            data = JSON.parse(data);
        }
        // data = data && data.length ? data[0] : [];
        if (data && data.length && JSON.stringify(data[0]) !== "{}") {
            var appendixStr = "";
            data.forEach(function (item) {
                appendixStr += '<li><a target="_blank" href="' + item.filePath + '">' + item.fileName + '</a></li>';
            })
            $(dom).html(appendixStr);
        }
    };




