#!/usr/bin/env python

from __future__ import absolute_import

from markdown import Markdown
from markdown.odict import OrderedDict
from docutils import nodes


class SectionPostprocessor(object):
    def run(self, node):
        i = 0
        while i < len(node):
            if isinstance(node[i], nodes.section):
                for subnode in node[i + 1:]:
                    if isinstance(subnode, nodes.section) and subnode['level'] == node[i]['level']:
                        break
                    node.remove(subnode)
                    node[i] += subnode

                self.run(node[i])

            i += 1

        return node


class StripPostprocessor(object):
    def run(self, node):
        class FakeStripper(object):
            def strip(self):
                return node

        return FakeStripper()


class Serializer(object):
    def __call__(self, element):
        return self.visit(element)

    def visit(self, element):
        method = "visit_%s" % element.tag
        if not hasattr(self, method):
            raise RuntimeError('Unknown element: %r' % element)
        else:
            return getattr(self, method)(element)

    def make_node(self, cls, element):
        node = cls()
        if element.text and element.text != "\n":
            node += nodes.Text(element.text)
        for child in element:
            node += self.visit(child)
            if child.tail and child.tail != "\n":
                node += nodes.Text(child.tail)

        return node

    def visit_div(self, element):
        return self.make_node(nodes.container, element)

    def visit_headings(self, element):
        section = nodes.section(level=int(element.tag[1]))
        section += self.make_node(nodes.title, element)
        return section

    visit_h1 = visit_headings
    visit_h2 = visit_headings
    visit_h3 = visit_headings
    visit_h4 = visit_headings
    visit_h5 = visit_headings
    visit_h6 = visit_headings

    def visit_p(self, element):
        return self.make_node(nodes.paragraph, element)

    def visit_em(self, element):
        return nodes.emphasis(text=element.text)

    def visit_strong(self, element):
        return nodes.strong(text=element.text)

    def visit_code(self, element):
        return nodes.literal(text=element.text)

    def visit_ul(self, element):
        return self.make_node(nodes.bullet_list, element)

    def visit_ol(self, element):
        return self.make_node(nodes.enumerated_list, element)

    def visit_li(self, element):
        return self.make_node(nodes.list_item, element)

    def visit_pre(self, element):
        return nodes.literal_block(text=element[0].text)

    def visit_blockquote(self, element):
        return nodes.literal_block(text=element[0].text)


def md2node(text):
    md = Markdown()
    md.serializer = Serializer()
    md.stripTopLevelTags = False
    md.postprocessors = OrderedDict()
    md.postprocessors['section'] = SectionPostprocessor()
    md.postprocessors['strip'] = StripPostprocessor()
    return md.convert(text)
