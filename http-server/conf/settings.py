{
    '<default>': {
        'exclude-annotations': ['species'],
    },

    'twitter-tech': {
        'filter': [{'term':['Health']}, {'tech':['ehealth']}],
        'period': 60*60*1000,
		'map': False,
    },

    'pubtator-tech': {
        'filter': [{'medicine':['telemedicine']}, {'ai':['classifier']}],
        'exclude-annotations': ['species', 'cell-line', 'mutation'],
	},

    'pubtator-cardiac-failure': {
        'exclude-annotations': ['species', 'mutation'],
	},

    'pubtator-pancreatic-cancer': {
        'filter': [{'medicine':['surgery']}, {'chemical':['gemcitabine']}],
        'exclude-annotations': ['species', 'cell-line', 'ai', 'mutation'],
	},
}
