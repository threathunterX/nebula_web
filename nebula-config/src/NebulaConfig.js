//添加配置项
function addConfig(key, value, type) {
  var container = document.querySelector(".config-item-container");
  var items = container.querySelectorAll(".config-item");
  const name = items.length > 0 ? items[items.length - 1].querySelector('.config-text').name : '';
  var index = name.substring(4, name.length);
  index = Number(index) + 1;

  var item = document.createElement("div");
  item.className = "config-item";
  item.innerHTML = getConfigItem(index, type);

  var readOnly = (type === 'initConfig');
  if (readOnly) {
    item.querySelector(".config-text").setAttribute('readOnly', readOnly);
  }
  //赋值
  item.querySelector(".config-text").value = key ? key : "";

  var valueEle = item.querySelector(".config-value");
  if (value === undefined) {
    valueEle.value = "";
  } else {
    valueEle.value = value;
  }

  var delBtn = item.querySelector(".del-config");
  //注册删除事件
  delBtn.onclick = function (e) {
    var res = true;
    var itemText = document.querySelector('.config-text[name=text' + index + ']');
    if (itemText.readOnly) {
      res = confirm("是否删除配置" + itemText.value + "？");
    }
    if (res) {
      if (itemText.readOnly) {
        ajax({
          method: "delete",
          url: "/platform/config/" + itemText.value,
          onSuccess: function (data) {
            if (data.status === 0) {
              e.target.parentElement.remove();
              showPrompt("删除成功。");
            } else {
              showPrompt("删除失败：" + data.msg + "。");
            }
            setTimeout(function () {
              document.querySelector(".save-info").innerText = "";
            }, 4500);
          },
          onError: function (status) {
            if (status === 302) {
              showPrompt("删除失败：请使用nebula登录后再进行操作。");
            } else {
              showPrompt("删除失败。");
            }
          }
        });
      } else {
        e.target.parentElement.remove();
      }
    }
  };

  container.appendChild(item);
}

//获取配置项元素
function getConfigItem(index) {
  return '<input class="config-text" type="text" name="text' + index + '" placeholder="配置名"/>' +
    '<input class="config-value" type="text" name="value' + index + '" placeholder="配置值"/>' +
    '<button class="del-config" type="button" data-value="' + index + '">删除</button>';
}

//获取配置项元素
function showPrompt(msg) {

  document.querySelector(".save-info").innerText = msg;
}

//init
(function () {
  function getConfigData() {
    ajax({
      url: "/platform/config",
      onSuccess: function (data) {
        if (data.status === 0) {
          var values = data.values.sort(function (a, b) {
            return a.key < b.key ? -1 : 1;
          });
          for (var i = 0; i < values.length; i += 1) {
            addConfig(values[i].key, values[i].value, 'initConfig');
          }
        }
      },
      onError: function (status) {
        if (status === 302) {
          showPrompt("初始化失败：请使用nebula登录后再刷新页面。");
        } else {
          showPrompt("初始化失败。");
        }
      }
    });
  }

  //初始化获取数据
  getConfigData();

  var form = document.querySelector(".config-body");

  //表单提交，保存
  form.onsubmit = function (e) {
    e.preventDefault();

    var params = [];

    var container = e.currentTarget;

    //获取删除键上的参数
    var indexList = container.querySelectorAll(".del-config");
    for (var i = 0; i < indexList.length; i++) {
      //param赋值
      var index = indexList[i].dataset.value;
      var itemKey = container["text" + index].value;
      var itemValue = container["value" + index].value;

      params.push({
        key: itemKey,
        value: itemValue
      });
    }

    ajax({
      method: "post",
      url: "/platform/config",
      params: params,
      onSuccess: function (data) {
        if (data.status === 0) {
          var items = container.querySelectorAll('.config-text');
          for (var i = 0; i < items.length; i += 1) {
            items[i].readOnly = true;
          }
          showPrompt("保存成功。");
        } else {
          showPrompt("保存失败：" + data.msg + "。");
        }

        setTimeout(function () {
          document.querySelector(".save-info").innerText = "";
        }, 4500);
      },
      onError: function (status) {
        if (status === 302) {
          showPrompt("保存失败：请使用nebula登录后再进行操作。");
        } else {
          showPrompt("保存失败。");
        }
      }
    });
  };

}());
