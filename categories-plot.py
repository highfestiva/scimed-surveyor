#!/usr/bin/env python3

from bokeh.models import ColumnDataSource, CustomJS
from bokeh.plotting import figure


def create_category_hbar(category, data):
    '''Data in the format [('Label 1',52), ('Label 2, 148'), ...] in ascending order.'''
    labels = [k for k,v in data]
    ds = ColumnDataSource(dict(labels=labels, value=[v for k,v in data]))
    p = figure(y_range=labels, sizing_mode='stretch_both', tools=['tap'])
    p.hbar(y='labels', right='value', height=0.9, source=ds)
    ds.selected.js_on_change(
            'indices',
            CustomJS(args=dict(labels=labels),
                    code='''var label = labels[cb_obj.indices[0]];
                            var url = new URL(window.location.href);
                            var category = "%s";
                            var lst = url.searchParams.get(category) || [];
                            if (typeof lst.push !== "function") {
                                lst = [lst];
                            }
                            lst.push(label);
                            url.searchParams.set(category, lst);
                            window.location.assign(url);''' % category))
    return p


if __name__ == '__main__':
    from bokeh.io import show
    category = 'fruit'
    data = [('apple',5), ('banana',3), ('carrot',2.9), ('daikon',0.2), ('eggplant',1.8), ('fig',22), ('grape',25)]
    p = create_category_hbar(category=category, data=data)
    show(p)
