"""If python-markdown is installed expose an apply_markdown(text) function,
to convert markeddown text into html.  Otherwise just set apply_markdown to None.

See: http://www.freewisdom.org/projects/python-markdown/
"""

__all__ = ['apply_markdown']

try:
    import markdown
    import re
    
    class CustomSetextHeaderProcessor(markdown.blockprocessors.BlockProcessor):
        """Override markdown's SetextHeaderProcessor, so that ==== headers are <h2> and ---- headers are <h3>.
        
        We use <h1> for the resource name."""
    
        # Detect Setext-style header. Must be first 2 lines of block.
        RE = re.compile(r'^.*?\n[=-]{3,}', re.MULTILINE)
    
        def test(self, parent, block):
            return bool(self.RE.match(block))
    
        def run(self, parent, blocks):
            lines = blocks.pop(0).split('\n')
            # Determine level. ``=`` is 1 and ``-`` is 2.
            if lines[1].startswith('='):
                level = 2
            else:
                level = 3
            h = markdown.etree.SubElement(parent, 'h%d' % level)
            h.text = lines[0].strip()
            if len(lines) > 2:
                # Block contains additional lines. Add to  master blocks for later.
                blocks.insert(0, '\n'.join(lines[2:]))
            
    def apply_markdown(text):
        """Simple wrapper around markdown.markdown to apply our CustomSetextHeaderProcessor,
        and also set the base level of '#' style headers to <h2>."""
        extensions = ['headerid(level=2)']
        safe_mode = False,
        output_format = markdown.DEFAULT_OUTPUT_FORMAT

        md = markdown.Markdown(extensions=markdown.load_extensions(extensions),
                               safe_mode=safe_mode, 
                               output_format=output_format)
        md.parser.blockprocessors['setextheader'] = CustomSetextHeaderProcessor(md.parser)
        return md.convert(text)

except:
    apply_markdown = None