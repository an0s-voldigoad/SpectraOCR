#!/usr/bin/env python3
import os, re, sys, json, csv, shutil, subprocess, argparse
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytesseract

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


VERSION = "2.0.0"

RESET="\033[0m"; BOLD="\033[1m"; RED="\033[91m"; GREEN="\033[92m"
YELLOW="\033[93m"; BLUE="\033[94m"; MAGENTA="\033[95m"; CYAN="\033[96m"
WHITE="\033[97m"; GRAY="\033[90m"

BANNER = r"""
███████╗██████╗ ███████╗ ██████╗████████╗██████╗  █████╗      ██████╗  ██████╗██████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗    ██╔═══██╗██╔════╝██╔══██╗
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝███████║    ██║   ██║██║     ██████╔╝
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══██║    ██║   ██║██║     ██╔══██╗
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║██║  ██║    ╚██████╔╝╚██████╗██║  ██║
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝  ╚═════╝╚═╝  ╚═╝
"""

LAST = {"text": "", "source": "", "language": "eng", "confidence": 0.0, "iocs": {}}

def clear(): os.system("clear")
def sep(): print(GRAY + "─"*78 + RESET)
def pause(): input(GRAY + "\nPress ENTER to continue..." + RESET)
def banner():
    clear()
    print(CYAN+BANNER+RESET)
    print(BOLD+WHITE+"                         SpectraOCR"+RESET)
    print(GRAY+f"                 OCR & Security Intelligence v{VERSION}"+RESET)
    print()

def langs():
    try:
        p=subprocess.run(["tesseract","--list-langs"],capture_output=True,text=True,timeout=10)
        return [x.strip() for x in p.stdout.splitlines()
                if x.strip() and not x.lower().startswith("list of")]
    except Exception:
        return []

def select_language():
    ls=langs()
    if not ls:
        return "eng"
    print(BOLD+CYAN+"OCR Languages"+RESET); sep()
    for i,x in enumerate(ls,1): print(f"{GREEN}[{i:03d}]{RESET} {x}")
    print(f"\n{YELLOW}[M]{RESET} Multiple languages"); sep()
    while True:
        c=input(f"\n{CYAN}Select language > {RESET}").strip()
        if c.lower()=="m":
            v=input(f"{CYAN}Enter codes, e.g. eng+hin+ben > {RESET}").strip()
            if v and all(x in ls for x in v.split("+")): return v
            print(RED+"Invalid language code."+RESET); continue
        try:
            n=int(c)
            if 1<=n<=len(ls): return ls[n-1]
        except ValueError: pass
        print(YELLOW+"Invalid selection."+RESET)

def load_image(path):
    p=Path(os.path.expanduser(path.strip("\"'")))
    if not p.is_file(): raise FileNotFoundError(str(p))
    img=cv2.imread(str(p),cv2.IMREAD_COLOR)
    if img is None: raise RuntimeError("Unable to decode image.")
    return img

def clean_text(t):
    if not t: return ""
    out=[]
    for line in t.splitlines():
        line=line.replace("|"," ")
        line=re.sub(r"[ \t]+"," ",line).strip()
        if line: out.append(line)
    return "\n".join(out)

def tokens(t):
    return re.findall(r"[A-Za-z0-9\u0900-\u097F\u0A00-\u0AFF\u0B00-\u0B7F\u0C00-\u0C7F]+",t)

def norm(t): return " ".join(clean_text(t).upper().split())

def preprocess(img):
    h,w=img.shape[:2]
    scale=3 if max(h,w)<3000 else 2
    up=cv2.resize(img,(w*scale,h*scale),interpolation=cv2.INTER_CUBIC)
    gray=cv2.cvtColor(up,cv2.COLOR_BGR2GRAY)
    clahe=cv2.createCLAHE(clipLimit=2.5,tileGridSize=(8,8)).apply(gray)
    den=cv2.fastNlMeansDenoising(clahe,None,8,7,21)
    otsu=cv2.threshold(den,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    adap=cv2.adaptiveThreshold(den,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY,31,11)
    return [("gray",gray),("contrast",clahe),("denoised",den),
            ("otsu",otsu),("adaptive",adap),
            ("otsu_inv",cv2.bitwise_not(otsu)),
            ("adaptive_inv",cv2.bitwise_not(adap))]

def ocr_pass(img, language, psm):
    try:
        cfg=f"--oem 3 --psm {psm}"
        data=pytesseract.image_to_data(img,lang=language,config=cfg,
                                       output_type=pytesseract.Output.DICT)
        text=clean_text(pytesseract.image_to_string(img,lang=language,config=cfg))
        cs=[]
        for c in data.get("conf",[]):
            try:
                c=float(c)
                if c>=0: cs.append(c)
            except: pass
        conf=sum(cs)/len(cs) if cs else 0.0
        return text,conf,data
    except Exception:
        return "",0.0,{}

def score(text,conf):
    ws=tokens(text)
    if not ws: return -999
    s=conf+len(ws)*3
    s+=sum(2 for w in ws if len(w)>=3)
    s+=sum(2 for w in ws if len(w)>=5)
    return s

def word_fusion(img,language):
    candidates=[]
    for name,var in preprocess(img):
        _,_,d=ocr_pass(var,language,11)
        for i,t in enumerate(d.get("text",[])):
            t=clean_text(t)
            if not t: continue
            try: c=float(d["conf"][i])
            except: c=0
            if c<35: continue
            candidates.append({"text":t,"confidence":c,
                "x":int(d["left"][i]),"y":int(d["top"][i]),
                "w":int(d["width"][i]),"h":int(d["height"][i])})
    candidates.sort(key=lambda x:(x["y"],x["x"]))
    selected=[]
    for a in candidates:
        duplicate=False
        for b in selected:
            if norm(a["text"])!=norm(b["text"]): continue
            ac=(a["x"]+a["w"]/2,a["y"]+a["h"]/2)
            bc=(b["x"]+b["w"]/2,b["y"]+b["h"]/2)
            if abs(ac[0]-bc[0])+abs(ac[1]-bc[1])<100:
                if a["confidence"]>b["confidence"]:
                    selected.remove(b); selected.append(a)
                duplicate=True; break
        if not duplicate: selected.append(a)
    lines=[]
    for a in selected:
        cy=a["y"]+a["h"]/2; placed=False
        for line in lines:
            if abs(cy-line["cy"])<=max(25,a["h"]*.65):
                line["items"].append(a)
                line["cy"]=sum(x["y"]+x["h"]/2 for x in line["items"])/len(line["items"])
                placed=True; break
        if not placed: lines.append({"cy":cy,"items":[a]})
    lines.sort(key=lambda x:x["cy"])
    out=[]
    for line in lines:
        items=sorted(line["items"],key=lambda x:x["x"])
        ws=[]
        for a in items:
            t=clean_text(a["text"])
            if t and (not ws or norm(ws[-1])!=norm(t)): ws.append(t)
        if ws: out.append(" ".join(ws))
    text="\n".join(out)
    conf=sum(x["confidence"] for x in selected)/len(selected) if selected else 0
    return text,conf

def run_ocr(img,language):
    results=[]
    variants=preprocess(img)
    total=len(variants)*5; n=0
    for name,var in variants:
        for psm in (3,6,7,11,12):
            n+=1
            print(f"\r{CYAN}[OCR]{RESET} {n:02d}/{total} {name:<14} PSM {psm}",end="",flush=True)
            text,conf,_=ocr_pass(var,language,psm)
            if text and tokens(text):
                results.append({"text":text,"confidence":conf,"method":name,
                                "psm":psm,"score":score(text,conf)})
    print()
    ft,fc=word_fusion(img,language)
    if ft:
        results.append({"text":ft,"confidence":fc,"method":"word_fusion",
                        "psm":"multi","score":score(ft,fc)+25+len(tokens(ft))*8})
    results.sort(key=lambda x:x["score"],reverse=True)
    unique=[]
    for r in results:
        if not any(norm(r["text"])==norm(x["text"]) for x in unique):
            unique.append(r)
    return unique

# -------------------- IOC / SECURITY ANALYSIS --------------------

IP_RE=re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
URL_RE=re.compile(r"\b(?:https?://|ftp://|www\.)[^\s<>\"]+",re.I)
EMAIL_RE=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
DOMAIN_RE=re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b",re.I)
MD5_RE=re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{32}(?![A-Fa-f0-9])")
SHA1_RE=re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{40}(?![A-Fa-f0-9])")
SHA256_RE=re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])")
CVE_RE=re.compile(r"\bCVE-\d{4}-\d{4,7}\b",re.I)
PATH_RE=re.compile(r"(?:/[\w.\-]+){2,}|(?:[A-Za-z]:\\(?:[^\\\s]+\\)+[^\\\s]+)")
CRYPTO_RE=re.compile(r"\b(?:bitcoin|ethereum|wallet|seed phrase|private key|api key|secret key|password|passwd|token)\b",re.I)

def iocs(text):
    urls=sorted(set(URL_RE.findall(text)))
    ips=sorted(set(IP_RE.findall(text)))
    emails=sorted(set(EMAIL_RE.findall(text)))
    hashes=sorted(set(MD5_RE.findall(text)+SHA1_RE.findall(text)+SHA256_RE.findall(text)))
    cves=sorted(set(x.upper() for x in CVE_RE.findall(text)))
    paths=sorted(set(PATH_RE.findall(text)))
    domains=sorted(set(DOMAIN_RE.findall(text)))
    domains=[d for d in domains if not any(d in u for u in urls)]
    keywords=sorted(set(x.lower() for x in CRYPTO_RE.findall(text)))
    return {"ips":ips,"urls":urls,"emails":emails,"domains":domains,
            "hashes":hashes,"cves":cves,"paths":paths,"security_keywords":keywords}

def security_analysis(text):
    found=iocs(text)
    banner(); print(BOLD+"Cybersecurity Analysis"+RESET); sep()
    labels=[("ips","IP Addresses"),("urls","URLs"),("domains","Domains"),
            ("emails","Email Addresses"),("hashes","Hashes"),("cves","CVE IDs"),
            ("paths","File Paths"),("security_keywords","Security Keywords")]
    total=0
    for key,label in labels:
        print(f"\n{CYAN}{label}{RESET}")
        if found[key]:
            for x in found[key]: print(f"  {GREEN}•{RESET} {x}")
            total+=len(found[key])
        else: print(f"  {GRAY}None detected{RESET}")
    print(f"\n{BOLD}Total indicators: {total}{RESET}")
    return found

def show_ioc():
    if not LAST["text"]:
        print(YELLOW+"[!] Run OCR first."+RESET); pause(); return
    LAST["iocs"]=security_analysis(LAST["text"]); pause()

# -------------------- FILE / PDF / BATCH --------------------

def do_image_ocr():
    banner(); print(BOLD+"Advanced Image OCR"+RESET); sep()
    path=input(f"\n{CYAN}Image path > {RESET}").strip()
    try: img=load_image(path)
    except Exception as e:
        print(RED+f"[✗] {e}"+RESET); pause(); return
    print(GREEN+f"[✓] Image loaded: {img.shape[1]}x{img.shape[0]}"+RESET)
    language=select_language()
    results=run_ocr(img,language)
    banner(); print(BOLD+"Extracted Text"+RESET); sep()
    if results:
        best=max([r for r in results if len(tokens(r["text"]))>=2] or results,
                 key=lambda x:x["score"])
        print("\n"+CYAN+best["text"]+RESET)
        print("\n"); sep(); print(BOLD+"Top OCR Passes"+RESET); print()
        for i,r in enumerate(results[:10],1):
            p=r["text"].replace("\n"," ")
            if len(p)>72: p=p[:69]+"..."
            print(f"{GREEN}{i:02d}{RESET} {r['method']:<18} PSM {str(r['psm']):<8} "
                  f"{r['confidence']:6.2f}%  {GRAY}{p}{RESET}")
        LAST.update(text=best["text"],source=path,language=language,confidence=best["confidence"])
    else:
        print(YELLOW+"[!] No readable text detected."+RESET)
        LAST.update(text="",source=path,language=language,confidence=0)
    print("\n"); sep(); print("Language:",language); pause()

def pdf_ocr():
    banner(); print(BOLD+"PDF OCR"+RESET); sep()
    path=Path(os.path.expanduser(input(f"\n{CYAN}PDF path > {RESET}").strip().strip("\"'")))
    if not path.is_file(): print(RED+"[!] File not found."+RESET); pause(); return
    language=select_language()
    try:
        doc=pymupdf.open(str(path)); chunks=[]
        for i,page in enumerate(doc):
            existing=clean_text(page.get_text("text"))
            if existing:
                chunks.append(f"[Page {i+1}]\n{existing}")
            else:
                pix=page.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
                arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
                if pix.n==4: arr=cv2.cvtColor(arr,cv2.COLOR_RGBA2BGR)
                else: arr=cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
                results=run_ocr(arr,language)
                if results:
                    best=max(results,key=lambda x:x["score"])
                    chunks.append(f"[Page {i+1}]\n{best['text']}")
        text="\n\n".join(chunks)
        LAST.update(text=text,source=str(path),language=language,confidence=0)
        banner(); print(BOLD+"PDF Extracted Text"+RESET); sep(); print(text or YELLOW+"No text detected."+RESET); sep(); pause()
    except Exception as e:
        print(RED+f"[✗] {e}"+RESET); pause()

def batch_ocr():
    banner(); print(BOLD+"Batch OCR"+RESET); sep()
    folder=Path(os.path.expanduser(input(f"\n{CYAN}Folder path > {RESET}").strip()))
    if not folder.is_dir(): print(RED+"[!] Folder not found."+RESET); pause(); return
    language=select_language()
    exts={".png",".jpg",".jpeg",".bmp",".tif",".tiff",".webp"}
    files=[p for p in folder.rglob("*") if p.suffix.lower() in exts]
    if not files: print(YELLOW+"[!] No supported images found."+RESET); pause(); return
    output=folder/"spectraocr_batch.txt"
    with output.open("w",encoding="utf-8") as f:
        for n,p in enumerate(files,1):
            print(f"\n{CYAN}[{n}/{len(files)}]{RESET} {p}")
            try:
                results=run_ocr(load_image(str(p)),language)
                best=max(results,key=lambda x:x["score"]) if results else None
                text=best["text"] if best else ""
                f.write(f"\n===== {p} =====\n{text}\n")
            except Exception as e:
                f.write(f"\n===== {p} =====\nERROR: {e}\n")
    print(GREEN+f"\n[✓] Saved: {output}"+RESET); pause()

def preprocessing_menu():
    banner(); print(BOLD+"Image Preprocessing"+RESET); sep()
    src=input(f"\n{CYAN}Image path > {RESET}").strip()
    try: img=load_image(src)
    except Exception as e: print(RED+str(e)+RESET); pause(); return
    outdir=Path("spectraocr_preprocessed"); outdir.mkdir(exist_ok=True)
    for name,im in preprocess(img):
        cv2.imwrite(str(outdir/f"{name}.png"),im)
    print(GREEN+f"[✓] Saved preprocessing variants to {outdir}/"+RESET); pause()

def report():
    if not LAST["text"]:
        print(YELLOW+"[!] Run OCR first."+RESET); pause(); return
    found=LAST.get("iocs") or iocs(LAST["text"])
    out=Path("spectraocr_report")
    out.mkdir(exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    txt=out/f"report_{stamp}.txt"
    js=out/f"report_{stamp}.json"
    content=[
        "SpectraOCR Security Report",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Source: {LAST['source']}",
        f"Language: {LAST['language']}",
        "",
        "EXTRACTED TEXT",
        "----------------",
        LAST["text"],
        "",
        "INDICATORS",
        "----------------"
    ]
    for k,v in found.items():
        content.append(f"{k.upper()}:")
        content.extend("  "+x for x in v)
    txt.write_text("\n".join(content),encoding="utf-8")
    payload={"version":VERSION,"generated":datetime.now().isoformat(),
             "source":LAST["source"],"language":LAST["language"],
             "confidence":LAST["confidence"],"text":LAST["text"],"iocs":found}
    js.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    print(GREEN+f"[✓] TXT:  {txt}"+RESET)
    print(GREEN+f"[✓] JSON: {js}"+RESET)
    pause()

def system_check():
    banner(); print(BOLD+"System Check"+RESET); sep()
    print("Python:",sys.version.split()[0])
    print("OpenCV:",cv2.__version__)
    try: print("Tesseract:",pytesseract.get_tesseract_version())
    except: print(RED+"Tesseract: NOT FOUND"+RESET)
    print("Languages:",len(langs()))
    try: print("PyMuPDF:",pymupdf.__doc__.split()[1] if pymupdf.__doc__ else "installed")
    except: print("PyMuPDF: installed")
    pause()

def about():
    banner(); print(BOLD+"About SpectraOCR"+RESET); sep()
    print(f"Version: {VERSION}")
    print("Single-file Linux OCR and defensive security-analysis toolkit.")
    print("Supports multilingual OCR, PDF extraction, batch processing,")
    print("IOC extraction and TXT/JSON reporting.")
    pause()

def menu():
    while True:
        banner(); sep()
        print(f"""
{GREEN}[1]{RESET}  Advanced Image OCR
{GREEN}[2]{RESET}  PDF OCR
{GREEN}[3]{RESET}  Batch OCR
{GREEN}[4]{RESET}  Image Preprocessing
{GREEN}[5]{RESET}  Security Analysis
{GREEN}[6]{RESET}  IOC Extraction
{GREEN}[7]{RESET}  Generate Report
{GREEN}[8]{RESET}  Language Manager
{GREEN}[9]{RESET}  System Check
{GREEN}[A]{RESET}  About
{RED}[0]{RESET}  Exit
""")
        sep()
        c=input(f"\n{CYAN}SpectraOCR > {RESET}").strip().lower()
        if c=="1": do_image_ocr()
        elif c=="2": pdf_ocr()
        elif c=="3": batch_ocr()
        elif c=="4": preprocessing_menu()
        elif c=="5": show_ioc()
        elif c=="6": show_ioc()
        elif c=="7": report()
        elif c=="8":
            banner(); print(BOLD+"Installed Languages"+RESET); sep()
            for i,x in enumerate(langs(),1): print(f"{GREEN}[{i:03d}]{RESET} {x}")
            pause()
        elif c=="9": system_check()
        elif c=="a": about()
        elif c=="0":
            print(GREEN+"\n[✓] SpectraOCR exited."+RESET); return
        else:
            print(YELLOW+"[!] Invalid option."+RESET)

def main():
    parser=argparse.ArgumentParser(description="SpectraOCR")
    parser.add_argument("--version",action="store_true")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    if args.version:
        print("SpectraOCR",VERSION); return
    if args.check:
        system_check(); return
    menu()

if __name__=="__main__":
    try: main()
    except KeyboardInterrupt:
        print("\n"+YELLOW+"[!] Interrupted."+RESET)
        sys.exit(130)
