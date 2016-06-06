(function () {
    "use strict";
    var emojis = [
            "1","-1","100","angry","beers","birthday","bowtie","cold_sweat","dizzy_face","dog","flushed","ghost","heart_eyes","joy","kissing_heart","laughing","moneybag","muscle","ok_hand","pensive","pig","pray","rage","relieved","scream","clap","shit","skull","sleeping","sleepy","smile","sob","stuck_out_tongue_winking_eye","sunglasses","tada","tired_face","triumph","unamused","v","yum"
        ],
        rEmojis = new RegExp(":(" + emojis.join("|") + "):", "g");
    angular.module("emoji", []).filter("emoji", function () {
        return function (input) {
            return input.replace(rEmojis, function (match, text) {
                return "<i class='emoji emoji_" + text + "' title=':" + text + ":'>" + text + "</i>";
            });
        };
    });
}());
