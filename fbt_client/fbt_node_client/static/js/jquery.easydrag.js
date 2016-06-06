$.fn.extend({
  easydrag: function(options) {
    var move = false;
    var oldPoint = null;
    var oldOffset = null;
    var $dialog = options && 'dialog' in options ? options.dialog : $(this);
    var width = $dialog.css('width');
    var height = $dialog.css('height');

    $dialog.css({
        'position': 'fixed',
        'z-index': '997',
        'width': width,
        'height': height
    });
    $(this).css({'cursor': 'move'});

    $(this).mousedown(function(e) {
        move = true;
        oldPoint = {
            x: e.pageX,
            y: e.pageY
        };
        oldOffset = {
            x: e.pageX - $dialog.offset().left,
            y: e.pageY - $dialog.offset().top
        };
    });
    $(document).mousemove(function(e) {
        if(move) {
            var newPoint = {
                x: e.pageX,
                y: e.pageY
            };
            $dialog.css({
                left: newPoint.x - oldOffset.x,
                top: newPoint.y - oldOffset.y
            });
        }
    });
    $(document).mouseup(function(e) {
        move = false;
    });
  }
});
