/*
from: https://github.com/Coffa/angular-clamp
modified: spark 2015.11.16
*/
(function() {
  angular
    .module('directives.clamp', [])
    .directive('clamp', clampDirective);

  clampDirective.$inject = ['$timeout'];
  function clampDirective($timeout) {
    var directive = {
      restrict: 'A',
      link: linkDirective,
      scope: {
        content: '='
      }
    };

    return directive;

    function linkDirective(scope, element, attrs) {
      // $timeout(function() {
        var lineCount = 1, lineMax = +attrs.clamp;
        var lineStart = 0;
        if (!scope.content) return;
        var text = scope.content;
        var maxWidth = element[0].offsetWidth;
        var estimateTag = createElement();
        var charWidth = parseInt($(element).css("font-size"));
        var likelyCharNum = Math.floor(maxWidth / charWidth);

        element.empty();
        element.append(estimateTag);

        while(lineCount < lineMax) {
          estimateTag.html(text.slice(lineStart));
          if (estimateTag[0].offsetWidth <= maxWidth) {
            resetElement(estimateTag);
            return;
          } else {
            estimateTag.html(text.slice(lineStart, lineStart + likelyCharNum));
            if (estimateTag[0].offsetWidth > maxWidth) {
              var i = 1;
              while(true) {
                estimateTag.html(text.slice(lineStart, lineStart + likelyCharNum - i));
                if (estimateTag[0].offsetWidth <= maxWidth) {
                  lineStart += likelyCharNum - i;
                  lineCount++;
                  break;
                }
                i++;
              }
            } else if (estimateTag[0].offsetWidth < maxWidth) {
              var i = 1;
              while(true) {
                estimateTag.html(text.slice(lineStart, lineStart + likelyCharNum + i));
                if (estimateTag[0].offsetWidth >= maxWidth) {
                  if (estimateTag[0].offsetWidth > maxWidth) {
                    i--;
                    estimateTag.html(text.slice(lineStart, lineStart + likelyCharNum + i));
                  }
                  lineStart += likelyCharNum + i;
                  lineCount++;
                  break;
                }
                i++;
              }
            } else {
                  lineStart += likelyCharNum;
                  lineCount++;
            }
            resetElement(estimateTag);
            estimateTag = createElement();
            element.append(estimateTag);
        }
      }
      estimateTag.html(text.slice(lineStart));
      resetElement(estimateTag, true);
      //scope.$emit('clampCallback', element, attrs);
      // });
    }
  }

  return;

  function createElement() {
    var tagDiv = document.createElement('div');
    (function(s) {
      s.position = 'absolute';
      s.whiteSpace = 'pre';
      s.visibility = 'hidden';
      s.display = 'inline-block';
    })(tagDiv.style);

    return angular.element(tagDiv);
  }

  function resetElement(element, type) {
    element.css({
      position: 'inherit',
      overflow: 'hidden',
      display: 'block',
      textOverflow: (type ? 'ellipsis' : 'clip'),
      visibility: 'inherit',
      whiteSpace: 'nowrap',
      width: '100%'
    });
  }
})();
