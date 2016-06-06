'use strict';

app.factory('UtilFactory', function(){
	return {
		transVote: function(vote){
			if(!vote)
				return 0;
			if(vote < 1000)
				return vote;
			else if(vote == 1000)
				return "1k";
			else if(vote > 1000 && vote < 9999)
				return (vote/1000).toFixed(1)+"k";
			else 
				return (vote/10000).toFixed(1)+"w";
		}
	}
});