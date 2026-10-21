"""Local offline design checks, separate from production release acceptance."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent

def contrast(a, b):
    def lum(value):
        rgb = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(x*y for x, y in zip(linear, (.2126, .7152, .0722)))
    light, dark = sorted((lum(a), lum(b)), reverse=True)
    return round((light+.05)/(dark+.05), 2)

def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page()
        errors=[]
        requests=[]
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.on('request', lambda req: requests.append(req.url) if req.url.startswith('http') else None)
        for width, height in [(320,780),(375,812),(768,1024),(844,390),(1440,1000)]:
            page.set_viewport_size({'width':width,'height':height})
            for theme in ['light','dark']:
                for route in ['find','details','comparison','research']:
                    page.goto(ROOT.joinpath('index.html').as_uri()+'#'+route)
                    # Hash navigation preserves the document and its theme.
                    current_theme = page.evaluate('document.documentElement.dataset.theme || "light"')
                    if current_theme != theme:
                        page.locator('#theme').click()
                    assert page.evaluate('document.documentElement.dataset.theme || "light"') == theme
                    page.evaluate('document.activeElement.blur()')
                    page.wait_for_selector('h1')
                    overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    results.append({'width':width,'height':height,'theme':theme,'route':route,'no_overflow':not overflow})
                    assert not overflow, results[-1]
                    if width in (375,1440):
                        page.screenshot(path=str(ROOT/f'{route}-{width}-{theme}.png'),full_page=True)
        page.set_viewport_size({'width':375,'height':812})
        page.goto(ROOT.joinpath('index.html').as_uri())
        page.get_by_role('button',name='Requirements & coverage').click()
        assert page.locator('dialog').evaluate('(d)=>d.open')
        page.keyboard.press('Escape')
        assert page.locator('#open-filters').evaluate('(e)=>e===document.activeElement')
        page.get_by_role('button',name='Add to shortlist',exact=True).click()
        assert page.locator('#saved-count').inner_text()=='1 shortlisted'
        page.get_by_placeholder('Model, CPU or part number').fill('unmatched')
        assert page.locator('#no-result').is_visible()
        page.get_by_placeholder('Model, CPU or part number').fill('')
        page.locator('summary').click()
        assert not page.locator('#fixture-ram').is_visible()
        page.locator('#fixture-count').select_option('10')
        assert page.locator('#fixture-ram').is_visible()
        page.locator('#fixture-count').select_option('9')
        assert page.locator('#remove-fixture').is_visible()
        page.locator('#low-range').focus()
        page.keyboard.press('ArrowRight')
        assert page.locator('#low-number').input_value()=='100'
        page.get_by_role('button',name='Explore options',exact=True).click()
        assert page.locator('#alternative').is_visible()
        page.goto(ROOT.joinpath('index.html').as_uri()+'#comparison')
        page.locator('#differences').check()
        assert page.get_by_role('rowheader',name='VRAM',exact=True).is_visible()
        assert page.get_by_role('rowheader',name='Storage',exact=True).count()==0
        page.locator('#right-choice').select_option('c')
        assert 'Not confirmed' in page.locator('#comparison-body').inner_text()
        page.emulate_media(reduced_motion='reduce')
        assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--motion").trim()')=='0ms'
        # Larger text reflow; not a substitute for a manual assistive-technology audit.
        page.evaluate('document.documentElement.style.fontSize="200%"')
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not errors, errors
        assert not requests, requests
        browser.close()
    pairs={
        'light body':('#182e27','#ffffff'),'light secondary':('#52645b','#ffffff'),
        'light button':('#ffffff','#1d5942'),'light warning':('#76500a','#fff3d6'),
        'dark body':('#edf4ed','#192922'),'dark secondary':('#b1c6b8','#192922'),
        'dark button':('#132a1b','#a8dfb8'),'dark warning':('#f5d58e','#3e321b')}
    ratios={k:contrast(*v) for k,v in pairs.items()}
    assert min(ratios.values())>=4.5,ratios
    report={'scope':'isolated design preview, not production acceptance','layout_cases':results,
            'interaction_checks':'passed','contrast_ratios':ratios,'page_errors':errors,'remote_requests':requests}
    ROOT.joinpath('verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'layout_cases':len(results),'interactions':'passed','contrast':ratios}))

if __name__=='__main__':
    main()
