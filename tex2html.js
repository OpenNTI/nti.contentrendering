
if (phantom.state.length === 0) {
    phantom.state = 'math';
    phantom.open(phantom.args[0]);
} else {
    MathJax.Hub.Queue(function(){
						  jQuery.fn.outerhtml=function outerHTML(){
							  return jQuery("&lt;p&gt;").append(this.eq(0).clone()).html();
						  };

						  //If we have mathjax that has been scaled above 100% back it off
						  $("span.math span[style*='font-size:']").each(function()
																			{
																				mathEl = this;
																				sizeStr = mathEl.style.fontSize;

																				if( sizeStr.charAt(sizeStr.length - 1) ){
																					var sizeInt = parseInt(sizeStr.substring(0, sizeStr.length - 1));
																					if(sizeInt && sizeInt > 100){
																						mathEl.style.fontSize = '100%';

																					}
																				}



																			});

						  $(".tex2jax_process").each(function(){
								span = $(this);
    													 span.children("script").remove();
																	   console.log( jQuery("<p>").append(span.eq(0).clone()).html());
						  });
		phantom.exit();
					  });
}


