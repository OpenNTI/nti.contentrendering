//Return a dictionary of useful data as a json dictionary
if (phantom.state.length === 0) {
    phantom.state = 'contentSize';
    phantom.open(phantom.args[0]);
} else {
	//The page may contain mathjax so we want to give it a chance to process
	//And actually we may eventually have our own js pipeline we need to wait on
    MathJax.Hub.Queue(function(){

						  var pageInfo = {};
						  
						  //Grab some data about the scroll dimensions
						  pageInfo['scrollHeight'] = document.documentElement.scrollHeight;
						  pageInfo['scrollWidth'] = document.documentElement.scrollWidth;

						  pageInfo['NTIID'] = $('meta[name=NTIID]').attr('content');

						  //Grab data about outbound links
						  var myPageURL = document.URL;
						  var myPage = myPageURL.substr(myPageURL.lastIndexOf('/')+1);

						  var outgoingLinks = $('a:visible[href]:not([href*="'+myPage+'"])');

						  //We abuse a map here so we don't get duplicates.  Can we do this another way?
						  var outgoingPages = {};

						  for( var i = 0; i < outgoingLinks.length; i++ ){
							  var outgoingLink = $(outgoingLinks[i]).attr('href');

							  if( outgoingLink.indexOf('#') >= 0 ){
								  outgoingLink = outgoingLink.substr(0, outgoingLink.indexOf('#'));
							  }

							  if(outgoingLink){
								  outgoingPages[outgoingLink]=true;
							  }
							  
						  }

						  var opArray = [];

						  for( key in outgoingPages ){
							  opArray.push(key);
						  }

						  pageInfo['OutgoingLinks'] = opArray;

						  console.log(JSON.stringify(pageInfo));
						  phantom.exit();
					  });
}


