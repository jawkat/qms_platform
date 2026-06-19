import re
from markupsafe import Markup, escape


def _is_numbered_line(line):
    return re.match(r"^\s*\d+\s*(?:°|\)|\.|-)\s+", line) is not None


def _strip_number_prefix(line):
    return re.sub(r"^\s*\d+\s*(?:°|\)|\.|-)\s+", '', line)


def render_article_content(text, include_style=False):
    if not text:
        return Markup('')

    lowered = text.lower()
    if any(tag in lowered for tag in ('<p', '<br', '<div', '<ul', '<ol', '<table', '<blockquote')):
        return Markup(text)

    normalized = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    blocks = re.split(r"\n\s*\n", normalized)
    out = []

    for block in blocks:
        norm = re.sub(r"\n\s*,\s*", ", ", block)
        norm = re.sub(r"\n\s*(?=[a-zàâäéèêëîïôöûüùç])", ' ', norm, flags=re.I)
        norm = re.sub(r"[ \t]{2,}", ' ', norm)
        lines = [ln.strip() for ln in norm.split('\n') if ln.strip()]
        if not lines:
            continue

        frag_start_commas = sum(1 for ln in lines if ln.startswith(',') or ln.startswith(';'))
        frag_short_lower = sum(1 for ln in lines if ln and ln[0].islower() and len(ln) < 60)
        if frag_start_commas + frag_short_lower >= max(2, len(lines) // 2):
            cleaned = [ln.lstrip(' ,;') for ln in lines]
            paragraph = escape(' '.join(cleaned)).replace('\n', '<br>')
            out.append(f'<p class="styled-paragraph fade-in">{paragraph}</p>')
            continue

        bullet_marker_re = re.compile(r"^\s*[-\u2022\u2013\*]\s+")
        bullet_matches = [bool(bullet_marker_re.match(ln)) for ln in lines]
        if sum(bullet_matches) >= max(2, len(lines) // 2):
            out.append('<ul class="styled-list fade-in mb-1 ps-1">')
            for ln in lines:
                item = re.sub(r"^\s*[-\u2022\u2013\*]\s+", '', ln)
                out.append(f'<li class="mb-1">{escape(item)}</li>')
            out.append('</ul>')
            continue

        if len(lines) == 1:
            line0 = lines[0]
            markers = list(re.finditer(r'(?:^|\s)([a-zA-Z])\)\s+', line0))
            if len(markers) >= 2:
                first_idx = markers[0].start()
                if first_idx < 30 or ':' in line0[:first_idx]:
                    text = line0.strip()
                    items = []
                    for i, m in enumerate(markers):
                        start = m.end()
                        end = markers[i+1].start() if i+1 < len(markers) else len(text)
                        content = text[start:end].strip().rstrip(',')
                        items.append((m.group(1), content))
                    if len(items) >= 2:
                        intro = text[:markers[0].start()].strip()
                        if intro:
                            out.append(f'<p class="styled-paragraph fade-in">{escape(intro)}</p>')
                        for letter, content in items:
                            if re.search(r"\d+\.\s+", content):
                                parts2 = re.split(r"\s*\d+\.\s*", content)
                                main = parts2[0].strip(' :;,-')
                                subitems = [p.strip().rstrip(' ,') for p in parts2[1:] if p.strip()]
                                out.append(f'<p class="styled-paragraph fade-in">{escape(letter)}) {escape(main)};</p>')
                                out.append('<ol class="styled-list mb-1 ps-4">')
                                for s in subitems:
                                    out.append(f'<li class="mb-1">{escape(s)}</li>')
                                out.append('</ol>')
                            else:
                                text_item = content
                                if not re.search(r"[;\.]\s*$", text_item):
                                    text_item = text_item.rstrip() + ' ;'
                                out.append(f'<p class="styled-paragraph fade-in">{escape(letter)}) {escape(text_item)}</p>')
                        out.append('<p class="styled-paragraph fade-in">&nbsp;</p>')
                        continue

        if len(lines) == 1 and re.search(r"\s[-\u2022\u2013\*]\s+", lines[0]):
            parts = re.split(r"\s[-\u2022\u2013\*]\s+", lines[0])
            if len(parts) > 1:
                intro = parts[0].strip()
                items = [p.strip() for p in parts[1:] if p.strip()]
                bad = any(it.startswith(',') or it.startswith(';') or it == '' for it in items)
                if not bad:
                    if intro:
                        out.append(f'<p class="styled-paragraph fade-in">{escape(intro)}</p>')
                    out.append('<ul class="styled-list fade-in mb-3 ps-3">')
                    for it in items:
                        out.append(f'<li class="mb-1">{escape(it)}</li>')
                    out.append('</ul>')
                    continue

        numbered_count = sum(1 for ln in lines if _is_numbered_line(ln))
        if numbered_count >= max(2, len(lines) // 2):
            out.append('<ol class="styled-list fade-in mb-3 ps-4">')
            for ln in lines:
                content = _strip_number_prefix(ln) if _is_numbered_line(ln) else ln
                out.append(f'<li class="mb-1">{escape(content)}</li>')
            out.append('</ol>')
            out.append('<p class="styled-paragraph fade-in">&nbsp;</p>')
            continue

        first = lines[0].lstrip()
        if first.startswith(('"', '"', '«', "'")):
            quote_html = ['<blockquote class="styled-quote fade-in">']
            for ln in lines:
                quote_html.append(f'<p>{escape(ln)}</p>')
            quote_html.append('</blockquote>')
            out.append('\n'.join(quote_html))
            continue

        paragraph_text = ' '.join(lines)
        paragraph = escape(paragraph_text).replace('\n', '<br>')
        out.append(f'<p class="styled-paragraph fade-in">{paragraph}</p>')

    html = badge + '\n'.join(out) if 'badge' in dir() else '\n'.join(out)
    return Markup(html)
