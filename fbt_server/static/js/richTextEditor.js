angular.module('richTextEditor', [])
  .service('rte', function($rootScope) {
    var self = this;
    self.editContent = '';


    //设置编辑内容，也就是说初始化后内容不为空
    self.setEditContent = function(content) {
      self.editContent = content;
    };

    self.clearContent = function() {
      tinymce.activeEditor.setContent('');
    };

    this.getContent = function() {
      return tinymce.activeEditor.getContent();
    };

    this.getRawContent = function() {
      return tinymce.activeEditor.getContent({
        'format': 'text'
      });
    };
    this.defaultInit = function() {
      self.init('#mytextarea', 'default');

    };
    this.simpleInit = function() {
      self.init('#mytextarea', 'simple');

    };

    self.init = function(selector, mode) {
      if (mode === 'default') {
        tinymce.init({
          selector: selector,
          language: 'zh_CN',
          plugins: [
            'imageuploadtoqiniu',
            'attachment',
            'table',
            'contextmenu',
            'searchreplace',
            'charmap',
            'advlist',
            'hr',
            'link',
            'autolink',
            'fullpage',
            'autoresize',
            'wordcount',
            'paste',
          ],
          toolbar1: 'bold italic underline strikethrough subscript superscript  charmap  hr removeformat | undo redo cut copy paste searchreplace ',
          toolbar2: 'bullist numlist | outdent indent blockquote | link unlink image attachment',
          menubar: false,
          paste_as_text: true, //无格式粘贴
          tools: 'inserttable',
          autoresize_min_height: 200,
          autoresize_max_height: 400,
          content_style: "img {max-width:100%}",

          setup: function(editor) {
            self.setPlaceholder(editor, self.editContent || '给别人以知识，给自己以鼓舞！');
          },

          init_instance_callback: function(editor) {
            editor.setContent(self.editContent || '给别人以知识，给自己以鼓舞！');
            editor.isDefault = !self.editContent;
          },
        });


      } else if (mode === 'simple') {

        tinymce.init({
          selector: selector,
          language: 'zh_CN',
          plugins: [
            'link',
            'autolink',
            'fullpage',
            'autoresize',
            'wordcount',
            'paste',
            'imageuploadtoqiniu',
          ],
          paste_as_text: true, //无格式粘贴
          menubar: false,
          autoresize_min_height: 200,
          autoresize_max_height: 500,

          toolbar1: 'bold italic underline removeformat |  bullist numlist  blockquote | link unlink | image',

          setup: function(editor) {
            self.setPlaceholder(editor, self.editContent || '(可选)问题背景、条件等信息，让同学更好地理解你的问题！');
          },

          init_instance_callback: function(editor) {
            editor.setContent(self.editContent || '(可选)问题背景、条件等信息，让同学更好地理解你的问题！');
            editor.isDefault = !self.editContent;
          },
        });

      }


    };

    this.setPlaceholder = function(editor, placeholderContent) {
      if (typeof placeholderContent !== undefined && placeholderContent !== false) {
        editor.isDefault = false;
        var defaultContent = '<!DOCTYPE html>\n<html>\n<head>\n</head>\n<body>\n\n</body>\n</html>';
        editor.on('init', function() {
            var cont = editor.getContent();
            if (cont == defaultContent) {
              editor.setContent(placeholderContent);
              cont = placeholderContent;
            }
            editor.isDefault = (cont === placeholderContent);
            if (!editor.isDefault) {
              return;
            }

          })
          .on('focus', function() {
            if (editor.isDefault) {
              editor.setContent('');
            }
          })
          .on('blur', function() {
            if (!editor.getContent() || (editor.getContent() === defaultContent)) {
              editor.setContent(placeholderContent);
            } else {
              editor.isDefault = false;
            }

          });
      }


    };

  })
  .constant('rteConfig', {

  })
  .directive('rte', ['rte', '$compile',

    function(rte, $compile) {
      return {
        replace: true,
        restrict: 'E',
        link: function(scope, elm, attrs) {

        },
        compile: function(elm, attrs) {
          return {

            post: function(scope, element, attributes, controller) {

              scope.init();
            }
          };

        },
        controller: function($scope, $element, $attrs) {
          var mode = $attrs.mode;
          if (mode === 'default') {
            $scope.init = function() {
              rte.defaultInit();

            };
          } else if (mode === 'simple') {

            $scope.init = function() {

              rte.simpleInit();
            };
          }
        },
        template: '<form method="post"><textarea id="mytextarea"></textarea></form>',
      };
    }
  ]);
