'use strict';
var publicJS = {
	init: function init() {
		this.tab();
		this.navOn();
	},
	isie9: function isie9() {
		if(navigator.appName == "Microsoft Internet Explorer" && parseInt(navigator.appVersion.split(";")[1].replace(/[ ]/g, "").replace("MSIE", "")) < 10) {
			return true;
		} else {
			return false
		}
	},
	tab: function tab() {
		var that = this;
		$('.js-tab').each(function(index, item) {
			var _this = $(this),
				initialSlide = 0;

			if(_this.attr('class').indexOf('focus') != -1) {
				initialSlide = 1;
			}
			_this.find('.hd li').eq(initialSlide).addClass('on');
			_this.find('.hd .more a').eq(initialSlide).show();

			that.tabsSwiper('.' + _this.attr('class').split(' ')[0], initialSlide);
		});
	},
	tabsSwiper: function tabsSwiper(box, initialSlide) {
		var that = this;
		var option = {
			speed: 500,
			initialSlide: initialSlide,
			on: {
				slideChange: function() {
					var _index = this.activeIndex;
					$(box).each(function() {
						var _this = $(this);
						_this.find(".hd .on").removeClass('on');
						_this.find(".hd li").eq(_index).addClass('on');

						if(_this.find('.more').length > 0) {
							_this.find('.more a').eq(_index).show().siblings().hide();
						}
					});
				},
			}
		}

		if(that.isie9()) {
			option = {
				speed: 500,
				initialSlide: initialSlide,
				// loop: true,
				onSlideChangeStart: function onSlideChangeStart() {
					$(box).each(function() {
						var _this = $(this);
						_this.find(".hd .on").removeClass('on');
						_this.find(".hd li").eq(tabsSwiper.activeIndex).addClass('on');

						if(_this.find('.more').length > 0) {
							_this.find('.more a').eq(tabsSwiper.activeIndex).show().siblings().hide();
						}
					});
				}
			}
		}

		var tabsSwiper = new Swiper(box + ' .tabSwiper', option);

		var _this = $(box);
		_this.find(".common_hd li").on('mouseenter', function(e) {
			var target;
			target = $(this);

			var i = target.index();

			_this.find(".common_hd li").removeClass('act');
			target.addClass('act');

			if(that.isie9()) {
				tabsSwiper.swipeTo(i);
			} else {
				tabsSwiper.slideTo(i);
			}

			if(_this.find('.more').length > 0) {
				_this.find('.more a').eq(i).show().siblings().hide();
			}
		});

		if($(window).width() < 991) {
			_this.find(".hd li a").on('click', function(e) {
				return false;
			});
		}

		if(!that.isie9() && window.matchMedia('(max-width: 991px)').matches && box == '.zwfw_box') {
			tabsSwiper.destroy(false);
		}
	},
	navOn: function tab() {
		if($.trim($('.BreadcrumbNav').text())!==''){
			$('.nav').find('li').each(function(){
				if($(this).find('a').text()==$.trim($.trim($('.BreadcrumbNav p').text()).split('>')[1])){
					$(this).addClass('on').siblings().removeClass('on');
				}
			})
		}else if(typeof ChannelsTag!=='undefined'){
			$('.'+ChannelsTag).addClass('on').siblings().removeClass('on');
			console.log($('.'+ChannelsTag).addClass('on').siblings().html());
		}else{
			$('.nav li:eq(0)').addClass('on').siblings().removeClass('on');;
		}
	}
}

$(function() {
	publicJS.init();

    
   
});




//pc端菜单点击
var myDivpc = $(".menudiv");
    $(".menu").click(function(event) {if($(this).attr("src") == 'images/menu.png') {
		$(this).attr("src", 'images/chahao.png');
		//$(".menudiv").css('display', "block");
		//$(".ywdiv").css("margin-top", "224px");
		//$(".tt").css("display", "none");
	} else {
		$(this).attr("src", 'images/menu.png');
		//$(".menudiv").css('display', "none");
		//$(".ywdiv").css("margin-top", "-105px");
		//$(".tt").css("display", "block");
	}
        // showDiv();//调用显示DIV方法
        $(myDivpc).toggle();
        $(document).one("click",
        function() { //对document绑定一个影藏Div方法
           $('.menu').attr("src", 'images/menu.png');
		//$(".menudiv").css('display', "none");
		$(myDivpc).hide();
	//$(".ywdiv").css("margin-top", "-105px");
		//$(".tt").css("display", "block");
        });

        event.stopPropagation(); //阻止事件向上冒泡
    });
    $(myDivpc).click(function(event) {

        event.stopPropagation(); //阻止事件向上冒泡
    });　
	
	 //  20230426 切换至电脑端
            $('.transToPc').on('click', function() {	
              var tempRadios = $(window).width() / 1280;
              $('meta[name=viewport]').attr('content', 'width=1280px, user-scalable=yes, initial-scale=' + tempRadios);
			  ztswiplist(ztItem, webSiteCode, '.ztswiper .swiper-wrapper');
              $('.transToPc').hide();
              $('.transToMobile').show();
            })
            $('.transToMobile').on('click', function() {
              $('meta[name=viewport]').attr('content',
                'width=device-width, user-scalable=yes, initial-scale=1.0, maximum-scale=3.0, minimum-scale=1.0');
              $('.transToPc').show();
              $('.transToMobile').hide();
            })
	　