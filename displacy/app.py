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


def build_hierplane_tree(tree: spacy.tokens.Doc) -> Dict[str, Any]:
    """
    Returns
    -------
    A JSON dictionary render-able by Hierplane for the given tree.
    """
    def node_constuctor(node):
        children = []
        for child in node.children:
            children.append(node_constuctor(child))

        span = node.text
        char_span_start = tree[node.i: node.i + 1].start_char
        char_span_end = tree[node.i: node.i + 1].end_char

        attributes = [node.pos_]

        if node.ent_iob_ == "B":
            attributes.append(node.ent_type_)

        if node.like_email:
            attributes.append("email")
        if node.like_url:
            attributes.append("url")

        hierplane_node = {
                "word": span,
                "nodeType": node.dep_,
                "attributes": attributes,
                "link": node.dep_,
                "spans": [{"start": char_span_start,
                           "end": char_span_end}]
        }
        if children:
            hierplane_node["children"] = children
        return hierplane_node

    hierplane_tree = {
            "text": str(tree),
            "root": node_constuctor(tree.root)
    }
    return hierplane_tree


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
        "tree": build_hierplane_tree(sentence)
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
