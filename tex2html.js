if (phantom.state.length === 0) {
    phantom.state = 'math';
    phantom.open(phantom.args[0]);
} else {
    MathJax.Hub.Queue(function(){
		console.log(document.body.innerHTML)
		phantom.exit()
	})
}
