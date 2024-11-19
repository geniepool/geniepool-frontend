#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json, urllib, re
import pandas as pd
from time import sleep

import dash
import flask
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table

import plotly.graph_objects as go


# In[ ]:


external_stylesheets = ['assets/GeniePool.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
server = app.server
app.title = "GeniePool"

@server.route('/GeniePool_API_documentation.pdf')
def serve_pdf():
    return flask.send_from_directory('assets', 'GeniePool_API_documentation.pdf')

#app.config['suppress_callback_exceptions'] = False
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-9GHT69HKHV"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);
          dataLayer.push({
              'pageTitle' : 'VARista'
          });}
          gtag('js', new Date());

          gtag('config', 'G-9GHT69HKHV');
        </script>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

default_style = {'width' : '57%', 'height' : '100%', 'font-family' : 'gisha', 'marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'center'}
chromosomes = [str(i) for i in range(1,23)] + ['X','Y','M']
info_style = {'width' : '100%', 'height' : '100%', 'font-family' : 'gisha', 'marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'left'}
study_style = {'marginBottom' : '10px', 'width' : '100%', 'paddingLeft' : '2px', 'borderWidth': '2px', 'borderStyle': 'groove', 'borderRadius': '5px', 'display' : 'inline-block', 'textAlign' : 'left'}
link_style = {'fontSize' : '125%', 'marginTop' : '2px', 'padding' : 6, 'borderWidth': '2px', 'borderStyle': 'groove', 'borderRadius': '5px', 'font-family' : 'gisha'}
SRA_studies_and_samples = pd.read_csv('assets/SRA_studies_and_samples.tsv', sep = '\t')
s3map = pd.read_csv('assets/S3.map', sep = '\t', header = None, names = ['version', 'reference', 'chromosome', 'modulus', 'id'])
s3map['chromosome'] = s3map['chromosome'].astype(str)
genes_to_coordinates = pd.read_parquet('assets/genes_to_coordinates.parquet')
geneNames = genes_to_coordinates['Gene'].tolist()
coordinatesInputPlaceHolder = 'Enter coordinate/s, Gene symbol or dbSNP name'
break_line = html.Hr(style={'height' : '4px', 'width' : '60%', 'color' : '#111111','display' : 'inline-block', 'marginLeft':'auto', 'marginRight':'auto'})


# In[ ]:


app.layout = html.Div([
    html.Div([
        html.Img(
            src = "assets/header.png",
            style={'width':'30%', 'float' : 'center', 'marginTop' : 5}
        ),
        
        html.Img(
            src = "assets/DCRC-logo.png",
            style={'width':'14%', 'float' : 'left'}
        ),
        
        html.Img(
            src = "assets/BirkLab_logo.png",
            style={'width':'17%', 'float' : 'right', 'marginTop' : 25}
        ),
        ],
        style={'width' : '100%', 'display' : 'inline-block','marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'center'}
    ),
    dcc.Location(id = 'location', refresh = False),
    
    html.Div([
        html.Div([
            dcc.RadioItems(
                id = 'coOccurrenceMode',
                options=[
                    {'label': 'Single variant', 'value': 'Single'},
                    {'label': 'Two variant co-occurrence', 'value': 'Compound'},
                ],
                value = 'Single',
                labelStyle = {'display': 'inline-block'},
                style = {'marginTop' : 0,'marginBottom' : 0, 'float' : 'center', 'width': '100%', 'display': 'inline-block', 'textAlign' : 'center'}
            ),
            html.P('Find samples with two different specific varaints. See FAQs for more information.', id = 'variantCoOccurenceDescription', style = {'display' : 'none'}),
            dcc.Input(
                id = 'coordinates',
                placeholder = coordinatesInputPlaceHolder,
                type = "_",
                style = {
                    'textAlign' : 'center',
                    'fontSize' : 20,
                    'font-family' : 'gisha',
                    'lineHeight' : '100%',
                    'borderWidth' : '2px',
                    'borderColor' : '#000044',
                    'width' : '55%',
                    'height' : '100%',
                    'padding': 24,
                    'borderRadius' : '5px',
                    'vertical-align' : 'top',
                    'marginTop' : 15,
                }
            ),
            dcc.Input(
                id = 'coordinates2',
                placeholder = 'Variant #2, e.g. 2:2000-C-G',
                type = "_",
                style = {
                    'display': 'none',
                }
            ),
            dcc.RadioItems(
                id = 'referenceRadioButtons',
                options=[
                    {'label': 'hg38', 'value': 'hg38'},
                    {'label': 'hg19', 'value': 'hg19'},
                    {'label': 'T2T', 'value': 'chm13v2'},
                ],
                value = 'hg38',
                labelStyle = {'display': 'inline-block'},
                style = {'marginTop' : 10,'marginBottom' : 10, 'float' : 'center', 'width': '100%', 'display': 'inline-block', 'textAlign' : 'center'}
            ),
            html.Div([
                html.P('Minimal coverage:', style = {'textAlign' : 'center', 'width': '15%', 'display': 'inline-block'}),
                dcc.Input(
                    id = 'ad_picker',
                    style = {'textAlign' : 'center', 'width': '20%', 'display': 'inline-block'},
                    placeholder = 'Coverage',
                    type = 'number',
                    min = 0,
                    max = 100,
                    step = 10,
                    value = 20
                ),
                html.P('Minimal quality:', style = {'textAlign' : 'center', 'width': '15%', 'display': 'inline-block'}),
                dcc.Input(
                    id = 'minqual_picker',
                    style = {'textAlign' : 'center', 'width': '20%', 'display': 'inline-block'},
                    placeholder = 'Quality',
                    type = 'number',
                    min = 0,
                    max = 1000,
                    step = 10,
                    value = 50
                ),
            ]),
            html.Br(),
            html.Details(
                [
                    html.Summary('AlphaMissense filtration (optional)', style = {'fontSize' : '100%'}),
                    html.Div(html.Div([
                        html.Div([
                            html.P('gnomAD filtration - if you are looking for rare variants', style = {'margin': 12, 'fontSize': '120%', 'font-weight' : 'bold'}),
                            html.P('Maximal homozygote count:', style = {'textAlign' : 'center', 'width': '25%', 'display': 'inline-block'}),
                            dcc.Input(
                                id = 'gnomad_nhomalt_picker',
                                style = {'textAlign' : 'center', 'width': '25%', 'display': 'inline-block', 'margin-top': 6, 'margin-bottom': 6},
                                type = 'number',
                                min = 0,
                                max = 10000,
                                step = 1
                            ),
                        ],
                        style = {'display': 'none'}
                        ),
                        html.Div([
                            html.P('Maximal allele count:', style = {'textAlign' : 'center', 'width': '25%', 'display': 'inline-block'}),
                            dcc.Input(
                                id = 'gnomad_nAC_picker',
                                style = {'textAlign' : 'center', 'width': '25%', 'display': 'inline-block'},
                                type = 'number',
                                min = 0,
                                max = 10000,
                                step = 1,
                            ),
                        ],
                        style = {'display': 'none'}
                    ),
                    #break_line,
                    html.Div([
                        html.P('AlphaMissense Filtration - if you are only interested in missense variants:', style = {'margin': 12, 'fontSize': '120%', 'font-weight' : 'bold'}),
                        dcc.Slider(
                            id = 'alphaMissense_slider',
                            min = 0,
                            max = 1,
                            step = 0.01,
                            marks={
                                0 : {'label': 'No filter', 'style': {'color': '#0d0d0d'}},
                                0.34 : {'label': '0.34', 'style': {'color': '#88c303'}},
                                0.564 : {'label': '0.564', 'style': {'color': '#f8b704'}},
                                1 : {'label': '1', 'style': {'color': '#f81504'}}
                            },
                            value = 0,
                        ),
                        html.P(id = 'alphaMissense_score'),
                        ],
                        style = {'width' : '75%', 'display' : 'inline-block','textAlign' : 'center'},
                        id = 'alphaMissense_filter_div'
                    ),
                    ], id = 'filter_div'),
                )
                ],
                id = 'Optional_filters'
            ),
            html.P(
                html.Button(
                    'Search',
                    id = 'search_button',
                    disabled = True,
                    n_clicks = 0,
                    style = {'align' : 'center', 'text-transform' : 'none', 'fontSize' : 24, 'padding' : 10, 'transform' : 'translateX(5%)', 'textAlign' : 'center'}
                ),
                style={'marginTop' : 20, 'width': '100%', 'display': 'inline-block','marginLeft':'auto', 'marginRight':'auto', 'textAlign' : 'center'}
            ),
            html.Br(),
        ],
        style={'float' : 'center', 'width' : '80%', 'marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'center'}),        
        ]
    ),
    
    html.Div(
        html.Div(
            [
             html.P('Howdy!', style = {'fontSize' : '150%'}),
             html.P(
                [
                'GeniePool makes thousands of NCBI\'s SRA exomes accessible.',
                html.Br(),
                'Enter coordinate/s (e.g. 7:117587750-117587780) for variants in the database.',
                html.Br(),
                'You can then select samples by study for more information - phenotypes, whether germline/somatic etc...',
                html.Br(),
                html.Br(),
                'Further information is available in our paper, which you are most welcome to read (and cite):',
                html.Br(),
                html.A('https://doi.org/10.1093/database/baad043', href = 'https://doi.org/10.1093/database/baad043', target = '_blank'),
                html.Br(),
                'Enjoy!',
                html.Br(),
                html.Br(),
                html.Details(
                    [
                    html.Summary('FAQs', style = {'fontSize' : '120%'}),
                    html.Div(html.Div(id = 'faq_div'))
                    ],
                id = 'faqs'),
                html.Br(),
                ],
                style = {'fontSize' : '120%', 'font-family' : 'gisha', 'line-height' : '1.5'},
            )],
            style = {'width' : '80%','textAlign' : 'left', 'align' : 'right', 'margin' : 'auto'},
        ),
        style = {'transform' : 'translate(9%,0%)', 'float' : 'center', 'width' : '100%','textAlign' : 'center', 'align' : 'center'},
        id = 'intro'
    ),
    
    html.Div(
        html.Div(
            id = 'table_div',
            style = {'width' : '80%', 'display' : 'inline-block','textAlign' : 'center', 'align' : 'center'}
        ),
        style = {'width' : '100%', 'display' : 'inline-block', 'textAlign' : 'center', 'align' : 'center'}
    ),
    
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    
    dcc.Store(id = 'coordinates_value'),
    dcc.Store(id = 'coordinates2_value'),
    dcc.Store(id = 'coOccurence_value'),
    dcc.Store(id = 'reference_genome'),
    dcc.Store(id = 'gnomADmaxHom'),
    dcc.Store(id = 'gnomADmaxAC'),
    dcc.Store(id = 'minAlphaMissense'),
    dcc.Store(id = 'n_click_track'),
    dcc.Store(id = 'studiesDict'),
    dcc.Store(id = 'variantNumber'),
    dcc.Store(id = 'minQual'),
    dcc.Store(id = 'minCoverage'),
    dcc.Store(id = 'tableData'),
    dcc.Download(id = 'download-dataframe-csv'),
])


# In[ ]:


def qna(question, answer):
    q = html.P('⸰ ' + question)
    a = html.P(answer)
    return [q, a]

@app.callback(
    [Output('faq_div', 'children')],
    [Input('faqs', 'open')]
)
def generateFAQs(isExpanded):
    if isExpanded == False:
        return [None]
    else:
        status = json.loads(requests.get('http://api.geniepool.link/rest/index/hg38/status').text)
        status = 'Last update: ' + '/'.join(status['update_date'].split(' ')[0].split('-')[::-1]) + ' - ' + '{:,}'.format(status['mutations_num']) + ' variants in ' + '{:,}'.format(status['samples_num']) + ' samples.'
        faqs = []
        faqs += qna('Is GeniePool free? Do I need to create a user to use it?',
                   'This website is free and open to all users and there is no login requirement.')
        faqs += qna('For what purposes should I use GeniePool?',
                    ['You can use GeniePool to look up specific variants and loci of interest. In contrast to similar tools, GeniePool links the results to specific studies.',
                    html.Br(),
                    'This means you can check if a variant or locus you are studying is already found in other individuals, what is written about them, to which study they belong etc.'])
        faqs += [html.Img(src = 'assets/demo.gif')]
        faqs += qna('When was the last update and how many variants and samples are in it?',
                    status)
        faqs += qna('What are "Minimal coverage" and "Minimal quality" scores?',
                   'GeniePool contains data from multiple studies that used various sequencing techniques, some are better than others. Therefore, to avoid noisy results (e.g. a homozygous variant detected by a single read sequence) you can choose to filter by the amount of reads that covered the location of the variant and the sequencing quality.')
        faqs += qna('Has AlphaMissense been integrated into GeniePool?',
                   'Yes! each missense variant has a colored circle - 🔴/🟡/🟢 - Hover your mouse over it to view the AlphaMissense score and prediction.')
        faqs += qna('What is the "Two variant co-occurrence" option?',
                    'GeniePool enables you to look for specific samples that have two different variants. To use this options, specific variants must be written in a chr:pos-ref-alt pattern and not a range, e.g. chr1:12345-A-C.')
        faqs += qna('Is the "Two variant co-occurrence" option suitable for finding compound-heterozygotes?',
                    'Yes and no. While you may be able to find samples with both input variants using the "Two Variant Co-occurrence" option, it does not guarantee that they are on different alleles. It is advisable to contact the uploader of the samples in question for confirmation.')
        faqs += qna('Why results don\'t include allele frequency for a variant from the GeniePool database?',
                   'While GeniePool contains data from many individuals, the data are derived from diverse studies that may have overrepresented data (e.g. shared samples or sequencing of multiple tumors from the same patient). Therefore, GeniePool should be used to assess whether a variant was previously found in a yes/no manner, and not to assess its frequency.')
        docs = html.Div([html.Span('Yes - you are welcome to check out its '),
                         html.A('documentation.', href = 'https://geniepool.link//GeniePool_API_documentation.pdf', target = '_blank')])
        faqs += qna('Does GeniePool comes with an Application Programming Interface (API)?', docs)
        github = html.Div([html.Span("Sure - it's on "),
                         html.A('GitHub.', href = 'https://github.com/geniepool', target = '_blank')])
        faqs += qna('Can I look at the code?', github)
        faqs += []
        return [faqs]

@app.callback(
    [Output('reference_genome', 'data')],
    [Input('referenceRadioButtons', 'value')]
)
def searchButtonAvailabilityStatus(value):
    return [value]


# In[ ]:


@app.callback(
    [Output('coordinates', 'placeholder'),
     Output('coordinates2', 'style'),
     Output('coOccurence_value', 'data'),
     Output('variantCoOccurenceDescription', 'style')],
    [Input('coOccurrenceMode', 'value')]
)
def searchButtonAvailabilityStatus(value):
    if value == 'Single':
        return [coordinatesInputPlaceHolder, {'display': 'none'}, value, {'display' : 'none'}]
    else:
        style = {
            'textAlign' : 'center',
            'fontSize' : 20,
            'font-family' : 'gisha',
            'lineHeight' : '100%',
            'borderWidth' : '2px',
            'borderColor' : '#000044',
            'width' : '55%',
            'height' : '100%',
            'padding': 24,
            'borderRadius' : '5px',
            'vertical-align' : 'top',
            'marginTop' : 25,
        }
        return ['Variant #1, e.g. 1:1000-A-T', style, value, {'display' : 'inline-block', 'float' : 'center', 'width': '100%'}]


# In[ ]:


@app.callback(
    [Output('minQual', 'data')],
    [Input('minqual_picker', 'value')]
)
def getMinQual(value):
    return [value]

@app.callback(
    [Output('minCoverage', 'data')],
    [Input('ad_picker', 'value')]
)
def getMinCoverage(value):
    return [value]

@app.callback(
    [Output('gnomADmaxHom', 'data')],
    [Input('gnomad_nhomalt_picker', 'value')]
)
def getMaxGnomAD_Hom(value):
    return [value]

@app.callback(
    [Output('gnomADmaxAC', 'data')],
    [Input('gnomad_nAC_picker', 'value')]
)
def getMaxGnomAD_AC(value):
    return [value]

@app.callback(
    [Output('minAlphaMissense', 'data'),
     Output('alphaMissense_score', 'children')],
    [Input('alphaMissense_slider', 'value')]
)
def getMinAlphaMissesnse(value):
    if value == 0:
        return [0, 'No AlphaMissense filtration']
    else:
        if value >= 0.564:
            prediction = 'Likely pathogenic'
        elif value >= 0.34:
            prediction = 'Ambigious'
        else:
            prediction = 'Likely benign'
        return [value, 'Output will include only missense variants with AlphaMissense score ≥ ' + str(value) + ' (' + prediction + ')']


# In[ ]:


@app.callback(
    [Output('search_button' , 'disabled'),
     Output('coordinates_value' , 'data'),
     Output('coordinates2_value' , 'data')],
    [Input('coordinates', 'value'),
     Input('coordinates2', 'value'),
     Input('coOccurence_value', 'data'),
     Input('reference_genome', 'data'),
     ]
)
def searchButtonAvailabilityStatus(value, value2, mode, reference):
    if mode == 'Single':
        if value == None:
            return [True, None, None]
        try:
            value = value.strip()
            if value.lower().startswith('rs'):
                if len(value) > 2:
                    if value[2:].isdigit():
                        return [False, value, None]
            if value.upper() in geneNames:
                gene = value.upper()
                value = genes_to_coordinates.query('Gene == @gene')[reference].values[0]
                return [False, value, None]
            chromosome, positions = value.split(':')
            positions = [position.strip().replace(' ','').replace(',','') for position in positions.split('-')]
            if chromosome.upper().replace('MT','M').replace('CHR','') not in chromosomes:
                return [True, value, None]
            if len(positions) not in (1,2):
                return [True, value, None]
            for position in positions:
                if position.isdigit() == False:
                    return [True, value, None]
            if len(positions) == 2:
                start, end = positions
                if int(start) > int(end) or int(end) - int(start) > 100000:
                    return [True, value, None]
            else:
                value = value + '-' + positions[0]
            return [False, value, None]
        except:
            return [True, value, None]
    else:
        for v in (value, value2):
            try:
                v = v.strip()
                chromosome = v.split(':')[0].upper().replace('MT','M').replace('CHR','')
                if chromosome not in chromosomes:
                    return [True, value, None]
                pos = v.split(':')[1].split('-')[0]
                if pos.isdigit() == False:
                    return [True, value, None]
                ref = str(v.split('-')[1])
                alt = str(v.split('-')[2])
                change = ref + alt
                if False in [i in 'ACTG' for i in change]:
                    return [True, value, None]
            except:
                return [True, value, None]
        return [False, value, value2]


# In[ ]:


def alphaMissenseScore(AlphaMissense):
    AlphaMissense = float(AlphaMissense)
    if AlphaMissense >= 0.564:
        result = 'AlphaMissense score = ' + str(AlphaMissense) + ' - Likely pathogenic'
    elif AlphaMissense >= 0.34:
        result = 'AlphaMissense score = ' + str(AlphaMissense) + ' - ambigious'
    else:
        result = 'AlphaMissense score = ' + str(AlphaMissense) + ' - Likely benign'
    return result

def generateToolTip(text, coordinate, variant, AlphaMissense):
    if 'missense' in text.lower() and AlphaMissense != '':
        chromosome, position = coordinate.split(':')
        return text + '\n\n' + alphaMissenseScore(AlphaMissense)
    else:
        return text

def annotateAlphaMissense(impact, AlphaMissense):
    if 'missense' not in impact.lower() or AlphaMissense == '':
        return impact
    else:
        AlphaMissense = float(AlphaMissense)
        if AlphaMissense >= 0.564:
            return impact + ' 🔴'
        elif AlphaMissense >= 0.34:
            return impact + ' 🟡'
        else:
            return impact + ' 🟢'
        

def generateDataTable(df):
    df['dbSNP'] = df['dbSNP'].apply(lambda x : '' if len(x) == 0 else '[' + x + '](https://www.ncbi.nlm.nih.gov/snp/' + x + ')')
    df['Impact'] = df.apply(lambda x : annotateAlphaMissense(x['Impact'], x['AlphaMissense']), axis = 1)
    def calculateFrequency(an, ac):
        if an == 0:
            return 0
        else:
            return round(ac/an*100,6)
    df['gnomAD frequency'] = df.apply(lambda x : calculateFrequency(x['gnomad_an'], x['gnomad_ac']), axis = 1)
    df = df.rename(columns={'gnomad_nhomalt': 'gnomAD homozygotes'})
    ddt = dash_table.DataTable(
        id = 'table',
        data = df.to_dict('records'),
        columns = [{'id': c, 'name': c, 'presentation': 'markdown'} if c == 'dbSNP' else {'id': c, 'name': c} for c in ['Coordinate','Variant','Homozygotes','Heterozygotes','Impact', 'gnomAD frequency', 'gnomAD homozygotes','dbSNP']],
        sort_action = 'native',
        sort_mode = 'single',
        row_selectable = 'single',
        page_action = 'native',
        page_current = 0,
        page_size = 25,
        filter_action='native',
        filter_options={"case": "insensitive"},
        css=[
            {
                "selector": ".dash-filter--case",
                "rule": "display: none",
            },
        ],
        fixed_rows={'headers' : True},
        style_cell = {
            'textAlign': 'left',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        tooltip_data=[
            {
                column: {'value': generateToolTip(str(value), row['Coordinate'], row['Variant'], row['AlphaMissense']), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('records')
        ],
        tooltip_duration=None,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(247, 247, 255)'
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': 'rgb(252, 252, 255)'
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "inherit !important",
                "border": "inherit !important",
            },
            {
                'if': {'filter_query': '{Ranks} = 1'},
                'backgroundColor': 'rgb(255, 255, 200)'
            },
            {
                'if': {'filter_query': '{Ranks} = 2'},
                'backgroundColor': 'rgb(255, 210, 130)'
            },
            {
                'if': {'filter_query': '{Ranks} = 3'},
                'backgroundColor': 'rgb(255, 220, 220)'
            },
        ],
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            },
        style_header = {
            'backgroundColor': 'rgb(220, 220, 255)',
            'fontWeight': 'bold',
            'whiteSpace' : 'normal'
            },
        style_table={
            'maxHeight': '250px',
            'maxwidth' : '150%',
            'border': 'thin lightgrey solid'
        },
        style_as_list_view = False
    )
    return ddt

def listVariants(chromosome, position, mutations):
    lines = []
    coordinate = chromosome + ':' + str(position)
    for mutation in mutations:
        ref = mutation['ref']
        alt = mutation['alt']
        
        dbSNP = ''
        if 'dbSNP' in mutation.keys():
            if mutation['dbSNP'].startswith('rs'):
                dbSNP = mutation['dbSNP']
        
        AlphaMissense = ''
        if 'alphamissense' in mutation.keys():
            AlphaMissense = mutation['alphamissense']
        hg38_coordinate = ''
        if 'hg38_coordinate' in mutation.keys():
            hg38_coordinate = mutation['hg38_coordinate']
        
        variant = ref + '>' + alt
        homs = mutation['hom']
        hets = mutation['het']
        try:
            impact = mutation['impact']
        except:
            impact = ''
        try:
            gnomad_an = mutation['gnomad_an']
        except:
            gnomad_an = 0
        try:
            gnomad_ac = mutation['gnomad_ac']
        except:
            gnomad_ac = 0
        try:
            gnomad_nhomalt = mutation['gnomad_nhomalt']
        except:
            gnomad_nhomalt = 0
        #print(coordinate, variant, homs, hets, impact, dbSNP, AlphaMissense, gnomad_an, gnomad_ac, gnomad_nhomalt, hg38_coordinate)
        lines.append([coordinate, variant, homs, hets, impact, dbSNP, AlphaMissense, gnomad_an, gnomad_ac, gnomad_nhomalt, hg38_coordinate])
    return lines

def geneToCoordinates(gene, referenceGenome):
    df = pd.read_csv('assets/' + referenceGenome + '_genes_to_coordinates.csv')
    coordinates = df[df['Gene'] == gene]['Coordinates'].values[0]
    return coordinates

def getAttributes(relevant_samples):
    relevant_samples = [[j['id'] for j in i] for i in relevant_samples]
    relevant_samples = set([item for sublist in relevant_samples for item in sublist])
    attributes_df = pd.read_parquet('assets/attributes.parquet')
    attributes = attributes_df[attributes_df['Run'].isin(relevant_samples)]['Attributes'].tolist()
    attributes = set([item for sublist in attributes for item in sublist])
    return attributes

def queryS3(x, pos_range):
    uri = 's3://genetics-repo/' + x['version'] + '/' + x['reference'] + '/chrom=chr' + x['chromosome'] + '/pos_bucket=' + str(x['modulus']) + '/part-' + x['id'] + '.snappy.parquet'
    df = pd.read_parquet(uri)
    df = df[df['pos'].isin(pos_range)]
    return df


@app.callback(
    [Output('download-dataframe-csv', 'data')],
    [Input('btn_csv', 'n_clicks'),
    Input('tableData', 'data')],
    prevent_initial_call = True,
)
def func(n_clicks, data):
    if n_clicks in (0, None):
        return [dash.no_update]
    else:
        df = pd.DataFrame(data)
        return [dcc.send_data_frame(df.to_csv, 'GeniePool.csv')]

@app.callback(
    [Output('table_div', 'children'),
     Output('n_click_track', 'data'),
     Output('intro', 'style'),
     Output('variantNumber', 'data'),
     Output('coordinates', 'value'),
     Output('location', 'search'),
     Output('tableData','data'),],
    [Input('search_button', 'n_clicks'),
     Input('coordinates_value','data'),
     Input('coordinates2_value','data'),
     Input('reference_genome', 'data'),
     Input('n_click_track', 'data'),
     Input('minQual', 'data'),
     Input('minCoverage', 'data'),
     Input('location', 'search'),
     Input('coOccurrenceMode', 'value'),
     Input('gnomADmaxHom', 'data'),
     Input('gnomADmaxAC', 'data'),
     Input('minAlphaMissense', 'data'),
     ]
)
def getAPI(n_clicks, coordinates, coordinates2, referenceGenome, search_button_n_clicks, minQual, minCoverage, query, mode, gnomADmaxHom, gnomADmaxAC, minAlphaMissense):
    inputUpdate = dash.no_update
    commonSamples = None
    if query.count('?') == 2:
        if n_clicks == None:
            search_button_n_clicks = 0
            n_clicks = 0
        if n_clicks == 0:
            referenceGenome = query.split('?')[1].split('reference=')[1]
            coordinates = query.split('?coordinates=')[1]
            inputUpdate = coordinates
            search_button_n_clicks = 0
            n_clicks = 1
    if n_clicks in [None, 0]:
        n_clicks = 0
        search_button_n_clicks = 0
        return [None, n_clicks, dash.no_update, dash.no_update, inputUpdate, '', dash.no_update]
    if n_clicks == search_button_n_clicks:
        return [dash.no_update, dash.no_update, dash.no_update, dash.no_update, inputUpdate, '', dash.no_update]
    if n_clicks > search_button_n_clicks:
        coordinates = coordinates.upper().replace(' ', '').replace(',','').replace('CHR','').replace('MT','').strip()
        if mode == 'Single':
            if coordinates.lower().strip().startswith('rs'):
                coordinates = coordinates.lower().strip()
            else:
                chromosome = coordinates.split(':')[0]
                pos = coordinates.split(':')[1]
                start, end = int(pos.split('-')[0]), int(pos.split('-')[1])
            try: #if end - start > -1:
                query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinates  + '?qual=' + str(minQual) + '&ad=' + str(minCoverage)
                if str(gnomADmaxHom) not in ('0', 'None'):
                    query += '&gnomad_nhomalt=' + str(gnomADmaxHom)
                if str(gnomADmaxAC) not in ('0', 'None'):
                    query += '&gnomad_ac=' + str(gnomADmaxAC)
                #query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinate
                print(query) #shit
                if minAlphaMissense != 0:
                    query += '&am=' + str(minAlphaMissense)
                print(query) #shit
                data = requests.get(query).text 
                data = json.loads(data)
                if len(data) == 0:
                    result = [html.P('No results')]
                    return [result, n_clicks, {'display':'none'}, None, inputUpdate,'']
                elif len(data) == 1:
                    lines = listVariants(chromosome, coordinates.split(':')[1].replace(',','').replace(' ',''), data['entries'])
                    variantNumber = len(lines)
                else:
                    variantNumber = int(data['count'])
                    df = pd.json_normalize(data['data'])
                    if df.empty:
                        result = [html.P('No results')]
                        return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
            except: #else:
                pos_range = range(start, end + 1)
                modulus1, modulus2 = start//100000, end//100000
                results = []
                for m in range(modulus1, modulus2 + 1):
                    expression = "reference == @referenceGenome and chromosome == @chromosome and modulus == @m"
                    query = s3map.query(expression)
                    query['S3'] = query.apply(lambda x : queryS3(x, pos_range), axis = 1)
                    results += [i for i in query['S3'].tolist() if i.empty == False]
                if len(results) == 0:
                    result = [html.P('No results')]
                    return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
                df = pd.concat(results)
                variantNumber = sum([len(i) for i in df['entries'].tolist()])
            if coordinates.lower().strip().startswith('rs'):
                chromosome = str(data).split("chrom': '")[1].split("'")[0].upper()
            data = df.apply(lambda x : listVariants(chromosome, x['pos'], x['entries']), axis = 1).tolist()
        else:
            chromosome1 = coordinates.split(':')[0]
            coordinate1 = coordinates.split(':')[1].split('-')[0]
            ref1 = coordinates.split('-')[1]
            alt1 = coordinates.split('-')[2]
            coordinates2 = coordinates.upper().replace(' ', '').replace(',','').replace('CHR','').replace('MT','').strip()
            chromosome2 = coordinates2.split(':')[0]
            coordinate2 = coordinates2.split(':')[1].split('-')[0]
            ref2 = coordinates2.split('-')[1]
            alt2 = coordinates2.split('-')[2]
            coordinates1 = chromosome1 + ':' + str(coordinate1) + '-' + str(coordinate1)
            coordinates2 = chromosome2 + ':' + str(coordinate2) + '-' + str(coordinate2)
            try: #if end - start > -1:
                query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinates1  + '?qual=' + str(minQual) + '&ad=' + str(minCoverage)
                if str(gnomADmaxHom) not in ('0', 'None'):
                    query += '&gnomad_nhomalt=' + str(gnomADmaxHom)
                if str(gnomADmaxAC) not in ('0', 'None'):
                    query += '&gnomad_ac=' + str(gnomADmaxAC)
                query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinates1
                if minAlphaMissense != 0:
                    query += '&am=' + str(minAlphaMissense)
                data = requests.get(query).text
                data = json.loads(data)
                if len(data) == 0:
                    result = [html.P('No results')]
                    return [result, n_clicks, {'display':'none'}, None, inputUpdate,'']
                elif len(data) == 1:
                    lines = listVariants(chromosome, coordinates.split(':')[1].replace(',','').replace(' ',''), data['entries'])
                    variantNumber = len(lines)
                else:
                    variantNumber = int(data['count'])
                    df1 = pd.json_normalize(data['data'])
                    df1 = df1[df1['entries'].apply(lambda x : "'ref': 'refX', 'alt': 'altX'".replace('refX', ref1).replace('altX', alt1) in str(x))]
                    if df1.empty:
                        result = [html.P('No results')]
                        return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
                    samples1 = [j for j in [i for i in df1['entries'].tolist()[0]] if (j['ref'] == ref1) and (j['alt'] == alt1)][0]
                    samples1 = [i['id'] for i in samples1['het']] + [i['id'] for i in samples1['hom']]
                sleep(1)
                query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinates2  + '?qual=' + str(minQual) + '&ad=' + str(minCoverage)
                if str(gnomADmaxHom) not in ('0', 'None'):
                    query += '&gnomad_nhomalt=' + str(gnomADmaxHom)
                if str(gnomADmaxAC) not in ('0', 'None'):
                    query += '&gnomad_ac=' + str(gnomADmaxAC)
                query = 'http://api.geniepool.link/rest/index/' + referenceGenome + '/' + coordinates2
                if minAlphaMissense != 0:
                    query += '&am=' + str(minAlphaMissense)
                data = requests.get(query).text
                data = json.loads(data)
                if len(data) == 0:
                    result = [html.P('No results')]
                    return [result, n_clicks, {'display':'none'}, None, inputUpdate,'']
                elif len(data) == 1:
                    lines = listVariants(chromosome, coordinates.split(':')[1].replace(',','').replace(' ',''), data['entries'])
                    variantNumber = len(lines)
                else:
                    variantNumber = int(data['count'])
                    df2 = pd.json_normalize(data['data'])
                    df2 = df2[df2['entries'].apply(lambda x : "'ref': 'refX', 'alt': 'altX'".replace('refX', ref2).replace('altX', alt2) in str(x))]
                    if df2.empty:
                        result = [html.P('No results')]
                        return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
                    samples2 = [j for j in [i for i in df2['entries'].tolist()[0]] if (j['ref'] == ref2) and (j['alt'] == alt2)][0]
                    samples2 = [i['id'] for i in samples2['het']] + [i['id'] for i in samples2['hom']]
                    commonSamples = list(set(samples1).intersection(set(samples2)))
                    if len(commonSamples) == 0:
                        result = [html.P('No results')]
                        return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
                    data1 = df1.apply(lambda x : listVariants(chromosome1, x['pos'], x['entries']), axis = 1).tolist()
                    data2 = df2.apply(lambda x : listVariants(chromosome2, x['pos'], x['entries']), axis = 1).tolist()
                    if data1 != data2:
                        data = data1 + data2
                    else:
                        data = data1
            except:
                result = [html.P('No results')]
                return [result, n_clicks, {'display':'none'}, None, inputUpdate,'', dash.no_update]
        lines = []
        for mutation in data:
            for line in mutation:
                hets = line[2]
                if len(hets) > 0:
                    legitHets = [i for i in hets if sum([int(v) for v in i['ad'].split(',')]) >= minCoverage and int(i['qual']) >= minQual]
                else :
                    legitHets = []
                homs = line[3]
                if len(homs) > 0:
                    legitHoms = [i for i in homs if sum([int(v) for v in i['ad'].split(',')]) >= minCoverage and int(i['qual']) >= minQual]
                else:
                    legitHoms = []
                if len(legitHets + legitHoms) != 0:
                    line[2] = legitHets
                    line[3] = legitHoms
                    lines += [line]
        if len(lines) == 0:
            result = [html.P('No results')]
            return [result, n_clicks, {'display':'none'}, None, inputUpdate, '', dash.no_update]
        df = pd.DataFrame(lines, columns = ['Coordinate', 'Variant', 'Homozygote Samples', 'Heterozygote Samples', 'Impact', 'dbSNP', 'AlphaMissense', 'gnomad_an', 'gnomad_ac', 'gnomad_nhomalt', 'hg38_coordinate'])
        if referenceGenome != 'chm13v2':
            del df['hg38_coordinate']
        df['Homozygotes'] = df['Homozygote Samples'].str.len()
        df['Heterozygotes'] = df['Heterozygote Samples'].str.len()
        if commonSamples != None:
            df = df[df['Variant'].isin([ref1 + '>' + alt1, ref2 + '>' + alt2])]
            df = df[df['Coordinate'].isin([coordinates1.split('-')[0], coordinates2.split('-')[0]])]
        ddt = generateDataTable(df)
        info = html.Div(id = 'info', style = info_style)
        bty_style = {
            'marginTop': '1',
            'font-family' : 'gisha',
            'marginRight': 3,
            'float': 'right',
            'fontSize': '100%',
            'padding' : 8,
            'display' : 'inline-block',
            'text-decoration' : 'none',
            'backgroundColor' : 'white',
            'border-radius' : 10
        }
        download_btn = html.Button('Download table', id = 'btn_csv', style = bty_style) #{'text-decoration' : 'none', 'fontSize' : '80%', 'float' : 'right', 'marginTop' : 1})
        samples = [i for i in df['Homozygote Samples'] if len(i) > 0] + [i for i in df['Heterozygote Samples'] if len(i) > 0]
        attributes = getAttributes(samples)
        for v in ('ENA ', 'DNA-ID', 'ENA-', 'External Id', 'INSDC'):
            attributes = [i for i in attributes if i.startswith(v) == False]
        explanation = 'The attributes are tags that characterize each sample on its BioSample page. Only variants associated with at least one sample that exhibits one or more of the selected attributes will be retained.'
        phenoPicker = html.Div(
            dcc.Dropdown(
                id = 'phenoPicker',
                options = [{'label': v, 'value': v} for v in sorted(attributes, reverse = False)],
                multi = True,
                placeholder = 'Select attributes ℹ️',
            ),
            title = explanation,
            style = {
                'width': '100%',
                'marginTop': '10px',
                'marginLeft': '10px',
                'marginRight': '10px',
                'font-family' : 'gisha',
                'marginLeft':'auto',
                'marginRight':'auto',
                'display' : 'inline-block'
            }
        ) 
        result = [phenoPicker, ddt, download_btn, info]
        if commonSamples != None:
            header = [html.P('Samples with both variants: (' + str(len(commonSamples)) + ')')]
            compounds = []
            for sample in commonSamples:
                compounds += [html.A(sample, href = 'https://www.ncbi.nlm.nih.gov/sra/' + sample, target = '_blank'), html.Span(', ')]
            result = header + [html.P(compounds[:-1])] + result
        return [result, n_clicks, {'display':'none'}, variantNumber, inputUpdate, '', df.to_dict('records')]
    else:
        return [None, n_clicks, dash.no_update, None, inputUpdate, '', dash.no_update]


# In[ ]:


def generateSamplesTable(df):
    df = df[['BioSample', 'Run', 'QUAL', 'Coverage']]
    df.columns = ['BioSample', 'SRA', 'Read Quality Score', 'Coverage (altered/total reads)']
    df['BioSample'] = df['BioSample'].apply(lambda x : '[' + x + '](https://www.ncbi.nlm.nih.gov/biosample/' + x + ')')
    df['SRA'] = df['SRA'].apply(lambda x : '[' + x + '](https://www.ncbi.nlm.nih.gov/sra/' + x + ')')
    df['Coverage (altered/total reads)'] = df['Coverage (altered/total reads)'].apply(lambda x : str(x.split(',')[1]) + '/' + str(int(x.split(',')[0]) +  int(x.split(',')[1])))
    table = dash_table.DataTable(
        data = df.to_dict('records'),
        columns = [{'id': c, 'name': c, 'presentation': 'markdown'} if c in ('BioSample', 'SRA') else {'id': c, 'name': c} for c in df.columns],
        row_deletable = False,
        css=[
            {
            "selector": ".dash-filter--case",
            "rule": "display: none",
            },
        ],
        fixed_rows={'headers' : True},
        style_cell = {
            'textAlign': 'left',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
            'font_size': 16,
            'font-family' : 'gisha'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto',
            },
        style_header = {
            'backgroundColor': 'rgb(220, 220, 255)',
            'fontWeight': 'bold',
            'whiteSpace' : 'normal'
            },
        style_table={
            'maxHeight': '250px',
            'maxwidth' : '120%',
            'border': 'thin lightgrey solid'
        },
        style_as_list_view = False
    )
    return table

def generateStudyBlock(study, homsInStudy, hetsInStudy):
    studyDivObject = []
    studyDivObject.append(html.Div(
        [html.Span('Study: ', style = {'font-family' : 'gisha'}),
         html.A(study, href = 'https://www.ncbi.nlm.nih.gov/bioproject/?term=' + study, target = '_blank', style = {'fontSize' : '125%', 'font-family' : 'gisha'})
        ], style = {'width' : '100%'})
    )
    if homsInStudy.empty == False:
        studyDivObject.append(html.P('Homozygotes: 🧬🧬 (' + str(homsInStudy.shape[0]) + ')', style={'fontSize' : 22, 'font-weight': 'bold', 'font-family' : 'gisha'}))
        table = generateSamplesTable(homsInStudy.copy())
        studyDivObject.append(html.Div(table, style={'width': '100%', 'display': 'inline-block','marginBottom':'10px','marginLeft':'auto', 'marginRight':'auto', 'textAlign' : 'left'}))
    if hetsInStudy.empty == False:
        studyDivObject.append(html.P('Heterozygotes: 🧬 (' + str(hetsInStudy.shape[0]) + ')', style={'fontSize' : 22, 'font-weight': 'bold', 'font-family' : 'gisha'}))
        table = generateSamplesTable(hetsInStudy.copy())
        studyDivObject.append(html.Div(table, style={'width': '100%', 'display': 'inline-block','marginBottom':'10px','marginLeft':'auto', 'marginRight':'auto', 'textAlign' : 'left'}))
    studyDivObject.append(html.Br())
    return studyDivObject

@app.callback(
    [Output('info', 'children'),
     Output('studiesDict', 'data')],
    [Input('table', 'derived_virtual_selected_rows'),
     Input('table', 'derived_virtual_data'),
     Input('referenceRadioButtons', 'value'),
     Input('variantNumber', 'data')]
)
def getVariantData(selected_row_index, data, referenceGenome, variantNumber):
    if selected_row_index in [[], None, None]:
        variantLimit = 1000
        if variantNumber > variantLimit:
            instructions = html.Div(
                [
                html.P('Too many variants in range (' + str(variantNumber) + ') - only first ' + str(variantLimit) + ' are shown.', style = {'font-family' : 'gisha'}),
                html.P('Pick a variant, then scroll down for more information.', style = {'font-family' : 'gisha'})
                ]
            )
        else:
            instructions = html.P('Pick a variant, then scroll down for more information', style = {'font-family' : 'gisha'})
        instructions_gif = html.Img(src = 'assets/click_demo.gif')
        return [[instructions, instructions_gif], None]
    else:
        coordinates = data[selected_row_index[0]]['Coordinate']
        mutation = data[selected_row_index[0]]['Variant']
        homozygotesData = data[selected_row_index[0]]['Homozygote Samples']
        homozygotes = {i['id'] : {'qual' : i['qual'], 'coverage' : i['ad']} for i in homozygotesData}
        heterozygotesData = data[selected_row_index[0]]['Heterozygote Samples']
        heterozygotes = {i['id'] : {'qual' : i['qual'], 'coverage' : i['ad']} for i in heterozygotesData}
        infoWindow = []
        
        ucsc_link = 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=' + referenceGenome + '&position=' + coordinates.replace(':','%3A')
        if referenceGenome == 'chm13v2':
            hg38_coordinate = data[selected_row_index[0]]['hg38_coordinate']
            ucsc_link = 'https://genome.ucsc.edu/cgi-bin/hgTracks?db=hub_3671779_hs1&position=' + hg38_coordinate
        ucscA = html.A('UCSC', href = ucsc_link, target = '_blank', style = link_style)
        
        if referenceGenome == 'hg38':
            gnomAD_Url = 'https://gnomad.broadinstitute.org/variant/' + coordinates.replace(':','-') + mutation.replace('>','-') + '?dataset=gnomad_r4'                          
        elif referenceGenome == 'hg19':
            gnomAD_Url = 'https://gnomad.broadinstitute.org/variant/' + coordinates.replace(':','-') + mutation.replace('>','-') + '?dataset=gnomad_r2_1' 
        elif referenceGenome == 'chm13v2':
            gnomAD_Url = 'https://gnomad.broadinstitute.org/variant/' + hg38_coordinate.replace(':','-') + mutation.replace('>','-') + '?dataset=gnomad_r4'
        else:
            None
        
        gnomADLink = html.A('gnomAD',target='_blank', href = gnomAD_Url, style = link_style)
        infoWindow.append(html.Div([html.P(''), ucscA, html.Span('    '), gnomADLink, html.P('')]))
        
        variant_df = SRA_studies_and_samples[SRA_studies_and_samples['Run'].isin(list(homozygotes.keys()) + list(heterozygotes.keys()))]
        studies_counts = variant_df['Study Title'].value_counts(sort = True)
        sorting_dict = {i : n for n, i in enumerate(studies_counts.index)}
        variant_df.sort_values(by=['Study Title'], key=lambda x: x.map(sorting_dict), inplace = True)
        variant_df.reset_index(drop = True, inplace = True)
        homs_df = variant_df[variant_df['Run'].isin(homozygotes.keys())]
        hets_df = variant_df[variant_df['Run'].isin(heterozygotes.keys())]
        homs_studies_counts = homs_df['Study Title'].value_counts()
        hets_studies_counts = hets_df['Study Title'].value_counts()
        
        xlabel = 'Click bars for specific information about studies'
        
        fig = go.Figure(
            data = [
                go.Bar(x = homs_studies_counts.index, y = homs_studies_counts.values, name = 'Homozygotes'),
                go.Bar(x = hets_studies_counts.index, y = hets_studies_counts.values, name = 'Heterozygotes')
            ],
            layout = go.Layout(
                title = 'Samples per study - ' + coordinates + ' ' + mutation,
                title_x = 0.5,
                barmode = 'relative',
                hovermode = 'x',
                xaxis = go.layout.XAxis(
                    title = 'Studies',
                    showticklabels = False,
                    categoryorder = 'total descending',
                ),
                yaxis = go.layout.YAxis(
                    title = 'Samples with variant'
                )
            )
        )
        graph = dcc.Graph(id = 'study_counts_graph', figure = fig)
        infoWindow.append(graph)
        infoWindow.append(html.Div(id = 'navigatorDiv'))
        
        displayLinks = True
        if len(studies_counts) > 1000:
            infoWindow.append(html.P('Links unavialable (over 1000 studies).'))
            return [infoWindow, None]
        
        infoWindow.append(html.Div(id = 'clickedStudy'))
        studiesDict = dict()
        studyDivObjects = []
        for study in studies_counts.index:
            homsInStudy = homs_df[homs_df['Study Title'] == study]
            homsInStudy['QUAL'] = homsInStudy['Run'].apply(lambda x : homozygotes[x]['qual'])
            homsInStudy['Coverage'] = homsInStudy['Run'].apply(lambda x : homozygotes[x]['coverage'])
            hetsInStudy = hets_df[hets_df['Study Title'] == study]
            hetsInStudy['QUAL'] = hetsInStudy['Run'].apply(lambda x : heterozygotes[x]['qual'])
            hetsInStudy['Coverage'] = hetsInStudy['Run'].apply(lambda x : heterozygotes[x]['coverage'])
            studyBlock = generateStudyBlock(study, homsInStudy, hetsInStudy)
            studiesDict[study] = html.Div(studyBlock, style = study_style)
            studyDivObjects.append(html.Div(studyBlock, style = study_style))
        details = html.Details([
            html.Summary('Click on a bar to view samples from a specific study, or here for all studies (' + str(len(studies_counts.index)) + ')', style = {'fontSize' : '125%'}),
            html.Div(html.Div(studyDivObjects))
        ],
        id = 'details')
        infoWindow.append(details)
        return [infoWindow, studiesDict]

@app.callback(
    [Output('clickedStudy', 'children')],
    [Input('study_counts_graph', 'clickData'),
     Input('studiesDict', 'data')])
def update_figure(clickData, studiesDict):
    if clickData == None:
        return [None]
    study = studiesDict[clickData['points'][0]['label']]
    study['props']['style'] = {'marginBottom' : '10px', 'width' : '100%', 'paddingLeft' : '2px', 'borderColor' : 'gold','borderWidth': '4px', 'borderStyle': 'groove', 'borderRadius': '5px', 'display' : 'inline-block', 'textAlign' : 'left'}
    return [[study]]


# In[ ]:


def extractSamples(samples):
    return re.findall(r"'id': '(.*?)'", str(samples))
    
@app.callback(
    [Output('table', 'data')],
    [Input('phenoPicker', 'value'),
    Input('tableData', 'data')]
)
def getRelevantVariants(chosen_attributes, data):
    if chosen_attributes == None:
        return [dash.no_update]
    elif len(chosen_attributes) == 0:
        return [pd.DataFrame(data).to_dict('records')]
    chosen_attributes = set(chosen_attributes)
    samples_in_range = pd.DataFrame(data)
    samples_in_range = samples_in_range['Homozygote Samples'] + samples_in_range['Heterozygote Samples']
    samples_in_range = [[j['id'] for j in i] for i in samples_in_range]
    samples_in_range = list(set([item for sublist in samples_in_range for item in sublist]))
    attributes_df = pd.read_parquet('assets/attributes.parquet')
    attributes_df = attributes_df[attributes_df['Run'].isin(samples_in_range)]
    samples = set()
    for sample in samples_in_range:
        try:
            sample_attributes = set(attributes_df[attributes_df['Run'] == sample]['Attributes'].values[0])
            if len(chosen_attributes & sample_attributes) > 0:
                samples.add(sample)
        except:
            continue
    df = pd.DataFrame(data)
    df['samples'] = df.apply(lambda x : set(extractSamples(x['Homozygote Samples']) + extractSamples(x['Heterozygote Samples'])), axis = 1)
    df = df[df['samples'].apply(lambda x : len(x & samples) > 0)]
    del df['samples']
    return [df.to_dict('records')]


# In[ ]:


if __name__ == '__main__':
    server.run(debug = False)

