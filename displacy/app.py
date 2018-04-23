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


def build_hierplane_tree(tree: spacy.tokens.Span) -> Dict[str, Any]:
    """
    Returns
    -------
    A JSON dictionary render-able by Hierplane for the given tree.
    """

    def node_constuctor(node: spacy.tokens.Token):
        children = []
        for child in node.children:
            children.append(node_constuctor(child))

        span = node.text
        # These character spans define what word is highlighted
        # by Hierplane. For intermediate nodes, the spans
        # are composed and the union of them is highlighted.
        char_span_start = tree[node.i: node.i + 1].start_char
        char_span_end = tree[node.i: node.i + 1].end_char

        # These are the icons which show up in the bottom right
        # corner of the node. We can add anything here,
        # but for brevity we'll just add NER and a few
        # other things.
        attributes = [node.pos_]

        if node.ent_iob_ == "B":
            attributes.append(node.ent_type_)

        if node.like_email:
            attributes.append("email")
        if node.like_url:
            attributes.append("url")

        hierplane_node = {
                "word": span,
                # The type of the node - all nodes with the same
                # type have a unified colour.
                "nodeType": node.dep_,
                # Attributes of the node, eg PERSON or "email".
                "attributes": attributes,
                # The link between  the node and it's parent.
                "link": node.dep_,
                # The span to highlight in the sentence.
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


def collapse_noun_phrases(document: spacy.tokens.Doc) -> None:
    for np in list(document.noun_chunks):
        np.merge(tag=np.root.tag_, lemma=np.root.lemma_,
                    ent_type=np.root.ent_type_)

@hug.get('/models')
def models():
    return {name: get_model_desc(nlp, name) for name, nlp in MODELS.items()}


@hug.post('/annotate')
def annotate(text: str, model: str, collapse_phrases: bool=False):

    nlp = MODELS[model]
    doc = nlp(text)
    trees = []
    for sentence in doc.sents:
        sentence_text = " ".join([x.text for x in sentence])
        # This is a little convoluted because we can't parse the
        # sentences twice because otherwise Spacy segfaults,
        # but we need the indices to be relative to the sentence
        # only for Hierplane.
        new_sentence = nlp(sentence_text)
        if collapse_phrases:
            collapse_noun_phrases(new_sentence)

        tree = build_hierplane_tree(next(new_sentence.sents))
        trees.append({"tree": tree, "sentence": sentence_text})
    
    return trees


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
