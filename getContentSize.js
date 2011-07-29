if (phantom.state.length === 0) {
    phantom.state = 'contentSize';
    phantom.open(phantom.args[0]);
} else {
	//The page may contain mathjax so we want to give it a chance to process
	//And actually we may eventually have our own js pipeline we need to wait on
    MathJax.Hub.Queue(function(){
						  console.log(document.documentElement.scrollHeight+' '+document.documentElement.scrollWidth);
		phantom.exit();
					  });
}


