/**
 * Rivet Software Inc.
 *
 * @copyright Copyright (c) 2006-2011 Rivet Software, Inc. All rights reserved.
 * Version 2.1.0.1
 *
 */

var moreDialog = null;
var Show = {
    Default:'raw',

    more:function( obj ){
        var bClosed = false;
        if( moreDialog != null )
        {
			try
			{
				bClosed = moreDialog.closed;
			}
			catch(e)
			{
				//Per article at http://support.microsoft.com/kb/244375 there is a problem with the WebBrowser control
				// that somtimes causes it to throw when checking the closed property on a child window that has been
				//closed.  So if the exception occurs we assume the window is closed and move on from there.
				bClosed = true;
			}

			if( !bClosed ){
				moreDialog.close();
			}
        }

        obj = obj.parentNode.getElementsByTagName( 'pre' )[0];
		var hasHtmlTag = false;
		var objHtml = '';
		var raw = '';

		//Check for raw HTML
		var nodes = obj.getElementsByTagName( '*' );
		if( nodes.length ){
			objHtml = obj.innerHTML;
		}else{
			if( obj.innerText ){
				raw = obj.innerText;
			}else{
				raw = obj.textContent;
			}

			var matches = raw.match( /<\/?[a-zA-Z]{1}\w*[^>]*>/g );
			if( matches && matches.length ){
				objHtml = raw;

				//If there is an html node it will be 1st or 2nd,
				//   but we can check a little further.
				var n = Math.min( 5, matches.length );
				for( var i = 0; i < n; i++ ){
					var el = matches[ i ].toString().toLowerCase();
					if( el.indexOf( '<html' ) >= 0 ){
						hasHtmlTag = true;
						break;
					}
				}
			}
		}

        if( objHtml.length ){
			var html = '';

			if( hasHtmlTag ){
				html = objHtml;
			}else{
				html = '<html>'+
					"\n"+'<head>'+
					"\n"+'    <title>Report Preview Details</title>'+
					"\n"+'    <style type="text/css">'+
					"\n"+'    body {'+
					"\n"+'    }'+
					"\n"+'    table {'+
					"\n"+'    }'+
					"\n"+'    </style>'+
					"\n"+'</head>'+
					"\n"+'<body>'+
						objHtml +
					"\n"+'</body>'+
					"\n"+'</html>';
			}

			moreDialog = window.open("","More","width=700,height=650,status=0,resizable=yes,menubar=no,toolbar=no,scrollbars=yes");
			moreDialog.document.write( html );
			moreDialog.document.close();

			if( !hasHtmlTag ){
				moreDialog.document.body.style.margin = '0.5em';
			}
        }
        else
        {
			//default view logic
			var lines = raw.split( "\n" );
			var longest = 0;

			if( lines.length > 0 ){
				for( var p = 0; p < lines.length; p++ ){
					longest = Math.max( longest, lines[p].length );
				}
			}

			//Decide on the default view
			this.Default = longest < 120 ? 'raw' : 'formatted';

			//Build formatted view
			var text = raw.split( "\n\n" ) >= raw.split( "\r\n\r\n" ) ? raw.split( "\n\n" ) : raw.split( "\r\n\r\n" ) ;
			var formatted = '';

			if( text.length > 0 ){
				if( text.length == 1 ){
					text = raw.split( "\n" ) >= raw.split( "\r\n" ) ? raw.split( "\n" ) : raw.split( "\r\n" ) ;
					formatted = "<p>"+ text.join( "<br /><br />\n" ) +"</p>";
				}else{
					for( var p = 0; p < text.length; p++ ){
						formatted += "<p>" + text[p] + "</p>\n";
					}
				}
			}else{
				formatted = '<p>' + raw + '</p>';
			}

			html = '<html>'+
				"\n"+'<head>'+
				"\n"+'    <title>Report Preview Details</title>'+
				"\n"+'    <style type="text/css">'+
				"\n"+'    body {'+
				"\n"+'       background-color: #f0f9ee;'+
				"\n"+'       font-family: Arial, san-serif; font-size: 0.8em;'+
				"\n"+'    }'+
				"\n"+'    table {'+
				"\n"+'       font-size: 1em;'+
				"\n"+'    }'+
				"\n"+'    </style>'+
				"\n"+'</head>'+
				"\n"+'<body>'+
				"\n"+'    <table border="0" width="100%">'+
				"\n"+'    <tr>'+
				"\n"+'        <td>'+
				"\n"+'            formatted: <a href="javascript:void(0);" onclick="opener.Show.toggle( window, this );">'+ ( this.Default == 'raw' ? 'as Filed' : 'with Text Wrapped' ) +'</a>'+
				"\n"+'        </td>'+
				"\n"+'    </tr>'+
				"\n"+'    <tr>'+
				"\n"+'        <td>'+
				"\n"+'            <div id="formatted" style="display: none;">'+formatted+'</div>'+
				"\n"+'        </td>'+
				"\n"+'    </tr>'+
				"\n"+'    <tr>'+
				"\n"+'        <td>'+
				"\n"+'            <pre id="raw" style="display: none; font-size: 1.2em;">'+raw+'</pre>'+
				"\n"+'        </td>'+
				"\n"+'    </tr>'+
				"\n"+'    </table>'+
				"\n"+'</body>'+
				"\n"+'</html>';

			moreDialog = window.open("","More","width=700,height=650,status=0,resizable=yes,menubar=no,toolbar=no,scrollbars=yes");
			moreDialog.document.write(html);
			moreDialog.document.close();

			this.toggle( moreDialog );
        }

		moreDialog.document.title = 'Report Preview Details';
    },

    toggle:function( win, domLink ){
        var domId = this.Default;

        var doc = win.document;
        var domEl = doc.getElementById( domId );
        domEl.style.display = 'block';

        this.Default = domId == 'raw' ? 'formatted' : 'raw';

        if( domLink ){
            domLink.innerHTML = this.Default == 'raw' ? 'with Text Wrapped' : 'as Filed';
        }

        var domElOpposite = doc.getElementById( this.Default );
        domElOpposite.style.display = 'none';
    },

	LastAR : null,
	showAR : function ( link, id, win ){
		if( Show.LastAR ){
			Show.hideAR();
		}

		var ref = link;
		do {
			ref = ref.nextSibling;
		} while (ref && ref.nodeName != 'TABLE');

		if (!ref || ref.nodeName != 'TABLE') {
			var tmp = win ?
				win.document.getElementById(id) :
				document.getElementById(id);

			if( tmp ){
				ref = tmp.cloneNode(true);
				ref.id = '';
				link.parentNode.appendChild(ref);
			}
		}

		if( ref ){
			ref.style.display = 'block';
			Show.LastAR = ref;
		}
	},

	toggleNext : function( link ){
		var ref = link;

		do{
			ref = ref.nextSibling;
		}while( ref.nodeName != 'DIV' );

		if( ref.style &&
			ref.style.display &&
			ref.style.display == 'none' ){
			ref.style.display = 'block';

			if( link.textContent ){
				link.textContent = link.textContent.replace( '+', '-' );
			}else{
				link.innerText = link.innerText.replace( '+', '-' );
			}
		}else{
			ref.style.display = 'none';

			if( link.textContent ){
				link.textContent = link.textContent.replace( '-', '+' );
			}else{
				link.innerText = link.innerText.replace( '-', '+' );
			}
		}
	},

	hideAR : function(){
		Show.LastAR.style.display = 'none';
	}
}