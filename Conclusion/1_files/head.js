var userName=getCookie('userName') ;
var userId=getCookie('netizenToken') ;
$(function(){
	var url=window.location.href;
	var codeNameLen=url.split("/").length;
	var codeName=url.split("/")[codeNameLen-3];
	if(codeName !== ""){
		$("."+codeName).addClass("on");
	$("."+codeName).siblings('li').removeClass('on');
	}	
	$('.login').attr('href',$('.login').attr('href')+'?backurl='+url);
	islogin();
	
	$('#out').click(function(){
		logout();//退出登录
	})
	//搜索
	$('#search span.icon').click(function(){
		search();
	})
	$('#search input').keydown(function(event){
	    if (event.keyCode== 13) {
	        search();
	    }
	})
	//$('.menu_button').click(function () {
      //$('.nav').fadeIn();
    //});
	var myDiv = $(".nav");
    $(".menu_button").click(function(event) {
        // showDiv();//调用显示DIV方法
        $(myDiv).toggle();
        $(document).one("click",
        function() { //对document绑定一个影藏Div方法
            $(myDiv).hide();
        });

        event.stopPropagation(); //阻止事件向上冒泡
    });
    $(myDiv).click(function(event) {

        event.stopPropagation(); //阻止事件向上冒泡
    });　　　　
function showDiv() {
    $(myDiv).fadeIn();
}
　　
    //$('.nav').click(function () {
     //$('.nav').fadeOut();
    //});
})
//是否登录
function search () {
	var searchWord=$('#search input').val();
console.log(searchWord)	
	if(searchWord=='请输入您要搜索的关键字'||searchWord==''){
			alert('请输入您要搜索的关键字');
	}else if(searchWord.length == 1){
		alert('请输入两个以上的关键字');
	}else{
		window.open('/search4/s?siteCode=bm89000001&searchWord='+encodeURIComponent(searchWord)+'&column=%25E5%2585%25A8%25E9%2583%25A8&left_right_index=0&searchSource=1')
	}
	
}
//是否登录
function islogin () {
	if(userName!==''||getCookie('userName')!==''){
		$('.my .userInfo .userName').text(userName+'，欢迎您！').attr('href', "/jbkzzx/c100074/common/list.html");
		$('.my .loginbox').hide();
		$('.my .userInfo').show();
	}
}
//退出登录
function logout(){
	$.ajax({
		url: "/communication/api-netizen/netizen/logout",
		type: "GET",
		contentType: "application/json",
		dataType: "JSON",
		headers: { 'token': userId },
		success: function (data) {
			if(data.status=='success'){
				clearCookie('mobile');
				clearCookie('idCard');
				clearCookie('netizenToken');
				clearCookie('userName');
				window.open('/jbkzzx/index.html','_self');
			}else if(data.status=='fail'){
				clearCookie('mobile');
				clearCookie('idCard');
				clearCookie('netizenToken');
				clearCookie('userName');
				location.reload(true);
			}
		}
	})
}
function getCookie (name) {
    var name = name + "=";
    var ca = document.cookie.split(";")
    var len = ca.length;

    for (var i = 0; i < len; i++) {
      var c = ca[i];
      while (c.charAt(0) == " ") c = c.substring(1);
      if (c.indexOf(name) == 0) { return c.substring(name.length, c.length); }
    }
    return '';
  }
function clearCookie(name) {
  var keys = document.cookie.match(/[^ =;]+(?=\=)/g);
  if (keys) {
    for (var i = keys.length; i--;) {
		console.log(keys[i])
		if(keys[i]==name){
			document.cookie = keys[i] + '=0;path=/;expires=' + new Date(0).toUTCString();
		}
      
      
    }
  }
}
