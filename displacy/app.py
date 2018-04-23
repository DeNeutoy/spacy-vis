# coding: utf8
from __future__ import unicode_literals

from typing import Dict, Any
import hug
from hug_middleware_cors import CORSMiddleware
import spacy

MODELS = {
    'en_core_web_sm': spacy.load('en_core_web_sm'),
    'de_core_news_sm': spacy.load('de_core_news_sm'),
    'es_core_news_sm': spacy.load('es_core_news_sm'),
    'pt_core_news_sm': spacy.load('pt_core_news_sm'),
    'fr_core_news_sm': spacy.load('fr_core_news_sm'),
    'it_core_news_sm': spacy.load('it_core_news_sm'),
    'nl_core_news_sm': spacy.load('nl_core_news_sm')
}


def build_hierplane_tree(tree: spacy.tokens.Doc, is_root: bool) -> Dict[str, Any]:
    """
    Returns
    -------
    A JSON dictionary render-able by Hierplane for the given tree.
    """
    children = []
    if is_root:
        node = tree.root
    else:
        node = tree

    for child in node.children:
        children.append(build_hierplane_tree(child, is_root=False))

    label = node.dep_
    span = " ".join([str(x) for x in node.subtree])
    hierplane_node = {
            "word": span,
            "nodeType": label,
            "attributes": [label],
            "link": label
    }
    if children:
        hierplane_node["children"] = children

    if is_root:
        hierplane_node = {
                "text": span,
                "root": hierplane_node
        }
    return hierplane_node


def get_model_desc(nlp, model_name):
    """Get human-readable model name, language name and version."""
    lang_cls = spacy.util.get_lang_class(nlp.lang)
    lang_name = lang_cls.__name__
    model_version = nlp.meta['version']
    return '{} - {} (v{})'.format(lang_name, model_name, model_version)


@hug.get('/models')
def models():
    return {name: get_model_desc(nlp, name) for name, nlp in MODELS.items()}


@hug.post('/annotate')
def annotate(text: str, model: str, collapse_phrases: bool=False):

    nlp = MODELS[model]
    doc = nlp(text)
    if collapse_phrases:
        for np in list(doc.noun_chunks):
            np.merge(tag=np.root.tag_, lemma=np.root.lemma_,
                        ent_type=np.root.ent_type_)

    sentence = next(doc.sents)

    return {
        "sentence": " ".join([str(x) for x in sentence]),
        "tree": build_hierplane_tree(sentence, is_root=True)
        }


@hug.post('/dep')
def dep(text: str, model: str, collapse_punctuation: bool=False,
        collapse_phrases: bool=False):
    """Get dependencies for displaCy visualizer."""
    nlp = MODELS[model]
    doc = nlp(text)
    if collapse_phrases:
        for np in list(doc.noun_chunks):
            np.merge(tag=np.root.tag_, lemma=np.root.lemma_,
                     ent_type=np.root.ent_type_)
    options = {'collapse_punct': collapse_punctuation}
    return spacy.displacy.parse_deps(doc, options)


@hug.post('/ent')
def ent(text: str, model: str):
    """Get entities for displaCy ENT visualizer."""
    nlp = MODELS[model]
    doc = nlp(text)
    return [{'start': ent.start_char, 'end': ent.end_char, 'label': ent.label_}
            for ent in doc.ents]


if __name__ == '__main__':
    import waitress
    app = hug.API(__name__)
    app.http.add_middleware(CORSMiddleware(app))
    waitress.serve(__hug_wsgi__, port=8080)
