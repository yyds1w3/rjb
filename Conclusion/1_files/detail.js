"use strict";

var ip = '';
// var ip = '';
var detailJs = {
  init: function init() {
    this.changeSize();
  },

  // 改变字体大小
  changeSize: function changeSize() {
    var fontsize = [20, 18, 16],
      lineheight = [38, 34, 30];

    var detailContent = $('#detailContent, #detailContent div, #detailContent p, #detailContent font, #detailContent span, #detailContent td');

    $('.changeSize span').on('click', function () {
      if ($(this).hasClass('on')) {
        return;
      }
      var i = $(this).index();

      $(this).addClass('on').siblings().removeClass('on');
      detailContent.css({ 'font-size': fontsize[i] + 'px', 'line-height': lineheight[i] + 'px' });
      console.log(i);
    });
  },
 
};

$(function () {
  detailJs.init();
 $("#changeSize span").eq(2).addClass("on").siblings("span").removeClass("on")
var ly=$('.ly').html();
if(ly=='来源：null'){
	$('.ly').hide();
}
	$('#detailContent .tinymce-annex').each(function(){
		if($(this).attr('data-href')!==''){
			var downname = $(this).text();
			$(this).html('<a href="'+$(this).attr('data-href')+'" download="'+downname+'">'+$(this).text()+'</a>');
		}
	})
	if(contentData.relationArticle){
		addAppendixArticle(contentData.relationArticle, '.article-appendix ul')
	}
	
});