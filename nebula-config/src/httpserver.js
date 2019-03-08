// 获取配置
function getConfig() {
  return {
    host: ''
  };
}

// ajax方法
function ajax(config) {
  var xmlhttp;
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp = new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
  }

  var method = config.method ? config.method : "GET";
  method = method.toUpperCase();

  var async = config.async === undefined ? true : config.async;

  //格式化参数
  var paramStr = prepareParams(config.params);

  var url = paramStr && method === "GET" ? config.url + "?" + paramStr : config.url;
  xmlhttp.open(method, getConfig().host + url, async);

  if (method === "GET") {
    xmlhttp.send();
  } else {
    xmlhttp.send(JSON.stringify(config.params));
  }

  //异步同步处理
  if (async) {
    //回调
    xmlhttp.onreadystatechange = function () {
      if (xmlhttp.readyState === 4) {

        ajaxCallBack(xmlhttp, config);
      }
    };
  } else {
    ajaxCallBack(xmlhttp, config);
  }
}

//ajax回调函数
function ajaxCallBack(xmlhttp, config) {

  if (xmlhttp.status === 200) {
    //处理返回数据
    var data = dealResponse(xmlhttp.responseText);

    // 未登录
    if (xmlhttp.responseURL.indexOf('/user') >= 0) {
      if (config.onError) {
        config.onError(302);
      }
    } else if (config.onSuccess) {
      config.onSuccess(data);
    }
  } else {
    if (config.onError) {
      config.onError(xmlhttp.status);
    }
  }
}

//参数格式化
function prepareParams(params) {

  var str = "";
  //非对象则不传参数
  if (typeof params !== "object") {
    return "";
  }
  for (var key in params) {

    str += key + "=" + params[key] + "&";
  }
  str = str.substr(0, str.length - 1);

  return str;
}

//参数格式化
function dealResponse(data) {
  try {
    return JSON.parse(data);
  } catch (e) {
    return {};
  }
}
