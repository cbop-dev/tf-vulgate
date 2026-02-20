import os
import glob
import re
import xml.etree.ElementTree as ET
from tf.fabric import Fabric
from tf.convert.walker import CV

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'tf'))
XML_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data', 'xml'))
VERSION = '0.1'

TF_PATH = f'{DATA_FOLDER}/{VERSION}'
TF = Fabric(locations=TF_PATH, silent=True)

slotType = 'word'

generic = {
    'name': 'Clementine Vulgate (Lemmatized)',
    'compiler': 'Derived from lascivaroma/latin-lemmatized-texts',
    'source': 'Lasciva Roma / PROIEL',
    'version': VERSION,
    'purpose': 'biblical research, morphological analysis'
}

otext = {
    'fmt:text-orig-full': '{text}{punc}',
    'sectionTypes': 'book,chapter,verse',
    'sectionFeatures': 'book,chapter,verse',
}

intFeatures = {
  'chapter',
  'verse'
}

featureMeta = {
    'chapter': {
        'description': 'Chapter number',
    },
    'verse': {
        'description': 'Verse number',
    },
    'book': {
        'description': 'Title of the book',    
    },
    'text': {
        'description': 'The textual content of a word',
    },
    'punc': {
        'description': 'Punctuation after a word',
    },
    'lemma': {
        'description': 'Dictionary base form of the word',
    },
    'pos': {
        'description': 'Part of Speech',
    },
    'morph': {
        'description': 'Morphological parsing attributes (Case, Number, Tense, Voice, etc.)',
    }
}

def remove_namespace(doc, namespace):
    ns = '{%s}' % namespace
    nsl = len(ns)
    for elem in doc.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]
    return doc

def get_xml_files():
    return sorted(glob.glob(os.path.join(XML_DIR, '*.xml')))

# We want the traditional order of books ideally, but the filenames are alphabetic (or urn based).
# Let's map URNs or titles to sort them, or simply process them as they come.
# For simplicity in this script, we'll sort them by URN suffix logically if possible,
# But since tlg0527.tlg001 is Genesis, `urn:cts:greekLit:tlg...` actually sorts reasonably well!
# tlg0527 = LXX (OT), tlg0031 = NT. We'll sort by filename.

def director(cv):
    xml_files = get_xml_files()
    
    cur = dict(
        book=None,
        chapter=None,
        verse=None,
    )
    
    for xml_file in xml_files:
        print(f"Processing {os.path.basename(xml_file)}...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        root = remove_namespace(root, 'http://www.tei-c.org/ns/1.0')
        
        # Get book title
        title_elem = root.find('.//title')
        book_title = title_elem.text.strip() if title_elem is not None else "Unknown Book"
        
        cur['book'] = cv.node('book')
        cv.feature(cur['book'], book=book_title)
        
        # Find chapters and verses
        # The structure is <ab type="chapter" n="urn:...:1">
        # Or <ab type="verse" n="urn:...:1.1">
        # In lascivaroma texts, verses look like they are inside the body separately or nested.
        # Let's traverse chronologically.
        
        # Actually, let's just find all <ab> tags.
        body = root.find('.//body')
        if body is None:
            continue
            
        for ab in body.findall('ab'):
            ab_type = ab.get('type')
            ab_n = ab.get('n', '')
            
            if ab_type == 'chapter':
                if cur['chapter']:
                    cv.terminate(cur['chapter'])
                    
                chapter_num = ab_n.split(':')[-1]
                cur['chapter'] = cv.node('chapter')
                cv.feature(cur['chapter'], chapter=int(chapter_num))
                
            elif ab_type == 'verse':
                if cur['verse']:
                    cv.terminate(cur['verse'])
                
                # verse_n is usually like 1.1 (Chap.Verse)
                verse_num_parts = ab_n.split(':')[-1].split('.')
                verse_num = verse_num_parts[-1] if len(verse_num_parts) > 0 else "1"
                
                # If there's no active chapter (rare but possible), create a dummy one
                if not cur['chapter']:
                    cur['chapter'] = cv.node('chapter')
                    cv.feature(cur['chapter'], chapter=int(verse_num_parts[0]) if len(verse_num_parts)>1 else 1)

                cur['verse'] = cv.node('verse')
                cv.feature(cur['verse'], verse=int(verse_num) if verse_num.isdigit() else verse_num)
                
                # Now iterate words in this verse
                for w in ab.findall('w'):
                    text = w.text.strip() if w.text else ""
                    
                    # USER Instruction: Ignore secondary enclitic nodes like {que}
                    if text.startswith('{') and text.endswith('}'):
                        continue
                        
                    lemma = w.get('lemma', '')
                    pos = w.get('pos', '')
                    morph = w.get('msd', '')
                    
                    # Create slot
                    slot = cv.slot()
                    
                    # For punctuation: since XML often drops punctuation or doesn't explicitly mark spaces between words,
                    # We will append a generic space to every word's punc field for now.
                    # If there's specific punctuation rendering needed, we would parse it.
                    # Looking at the sample, XML stripped most punctuation.
                    cv.feature(slot, text=text, punc=" ", lemma=lemma, pos=pos, morph=morph)

                cv.terminate(cur['verse'])
                cur['verse'] = None
                
        # Terminate chapter
        if cur['chapter']:
            cv.terminate(cur['chapter'])
            cur['chapter'] = None
            
        # Terminate book
        cv.terminate(cur['book'])
        cur['book'] = None

    print('\nINFORMATION:', cv.activeTypes(), '\n')

cv = CV(TF)
cv.walk(
    director,
    slotType,
    otext=otext,
    generic=generic,
    intFeatures=intFeatures,
    featureMeta=featureMeta,
)
