#!/usr/bin/env python3
"""
Batch‐submit bacterial FASTA to PHASTER URLAPI, poll until done,
and download the ZIP results per sample.
"""
import os, time, argparse
import requests
from tqdm import tqdm

API = "http://phaster.ca/phaster_api"
SUBDIR = "submissions"          # results HTML live at phaster.ca/submissions/<job>.*
ZIPPATH = "zip"                 # JSON “zip” field

def submit(fasta):
    with open(fasta, 'rb') as fh:
        r = requests.post(API, data=fh)
    r.raise_for_status()
    return r.json()['job_id']

def poll(job_id, interval=30):
    while True:
        r = requests.get(f"{API}?acc={job_id}")
        r.raise_for_status()
        js = r.json()
        status = js.get('status','')
        if status == "Complete":
            return js
        time.sleep(interval)

def download(url, outpath):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(outpath,'wb') as w:
        for chunk in r.iter_content(1024*8):
            w.write(chunk)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i','--input', required=True,
                   help='dir of FASTA (.fna/.fa/.fasta)')
    p.add_argument('-o','--output', required=True,
                   help='output dir for ZIP files')
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    fastas = [f for f in os.listdir(args.input)
              if f.lower().endswith(('.fna','.fa','.fasta'))]

    for fasta in tqdm(fastas, desc="Samples"):
        path = os.path.join(args.input, fasta)
        sample = os.path.splitext(fasta)[0]
        job = submit(path)
        meta = poll(job)
        zip_url = meta['zip']
        outzip = os.path.join(args.output, f"{sample}.zip")
        download(zip_url, outzip)

if __name__=="__main__":
    main()