#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json, urllib, re
import pandas as pd

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table

import plotly.graph_objects as go


# In[ ]:


external_stylesheets = ['assets/GeniePool.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "GeniePool"
app.config['suppress_callback_exceptions'] = False

default_style = {'width' : '57%', 'height' : '100%', 'font-family' : 'gisha', 'marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'center'}
chromosomes = [str(i) for i in range(1,23)] + ['X','Y','M']
info_style = {'width' : '100%', 'height' : '100%', 'font-family' : 'gisha', 'marginLeft' : 'auto', 'marginRight' : 'auto', 'textAlign' : 'left'}
study_style = {'marginBottom' : '10px', 'width' : '100%', 'paddingLeft' : '2px', 'borderWidth': '2px', 'borderStyle': 'groove', 'borderRadius': '5px', 'display' : 'inline-block', 'textAlign' : 'left'}
link_style = {'fontSize' : '125%', 'marginTop' : '2px', 'padding' : 6, 'borderWidth': '2px', 'borderStyle': 'groove', 'borderRadius': '5px', 'font-family' : 'gisha'}
SRA_studies_and_samples = pd.read_csv('assets/SRA_studies_and_samples.tsv', sep = '\t')
s3map = pd.read_csv('assets/S3.map', sep = '\t', header = None, names = ['version', 'reference', 'chromosome', 'modulus', 'id'])
s3map['chromosome'] = s3map['chromosome'].astype(str)


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
            dcc.Input(
                id = 'coordinates',
                placeholder = 'Enter coordinate/s...',# or gene symbol...',
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
                    'marginTop' : 25,
                }
            ),
            dcc.RadioItems(
                id = 'referenceRadioButtons',
                options=[
                    {'label': 'hg38', 'value': 'hg38'},
                    {'label': 'hg19', 'value': 'hg19'},
                ],
                value = 'hg38',
                labelStyle = {'display': 'inline-block'},
                style = {'marginTop' : 20,'marginBottom' : 10, 'float' : 'center', 'width': '100%', 'display': 'inline-block', 'textAlign' : 'center'}
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
    dcc.Store(id = 'reference_genome'),
    dcc.Store(id = 'n_click_track'),
    dcc.Store(id = 'studiesDict'),
    dcc.Store(id = 'variantNumber'),
    dcc.Store(id = 'minQual'),
    dcc.Store(id = 'minCoverage'),
    dcc.Store(id = 'tableData')
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
        status = json.loads(requests.get('http://geniepool-env-1.eba-ih62my9c.us-east-1.elasticbeanstalk.com/rest/index/hg38/status').text)
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
        faqs += qna('Why results don\'t include allele frequency for a variant?',
                   'While GeniePool contains data from many individuals, the data are derived from diverse studies that may have overrepresented data (e.g. shared samples or sequencing of multiple tumors from the same patient). Therefore, GeniePool should be used to assess whether a variant was previously found in a yes/no manner, and not to assess its frequency.')
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


# In[ ]:


@app.callback(
    [Output('search_button' , 'disabled'),
     Output('coordinates_value' , 'data')],
    [Input('coordinates', 'value')]
)
def searchButtonAvailabilityStatus(value):
    if value == None:
        return [True, None]
    try:
        value = value.strip()
        chromosome, positions = value.split(':')
        positions = [position.strip().replace(' ','').replace(',','') for position in positions.split('-')]
        if chromosome.upper().replace('MT','M').replace('CHR','') not in chromosomes:
            return [True, value]
        if len(positions) not in (1,2):
            return [True, value]
        for position in positions:
            if position.isdigit() == False:
                return [True, value]
        if len(positions) == 2:
            start, end = positions
            if int(start) > int(end) or int(end) - int(start) > 100000:
                return [True, value]
        else:
            value = value + '-' + positions[0]
        return [False, value]
    except:
        return [True, value]


# In[ ]:


def generateDataTable(df):
    df['dbSNP'] = df['dbSNP'].apply(lambda x : '' if len(x) == 0 else '[' + x + '](https://www.ncbi.nlm.nih.gov/snp/' + x + ')')
    ddt = dash_table.DataTable(
        id = 'table',
        data = df.to_dict('records'),
        columns = [{'id': c, 'name': c, 'presentation': 'markdown'} if c == 'dbSNP' else {'id': c, 'name': c} for c in ['Coordinate','Variant','Homozygotes','Heterozygotes','Impact', 'dbSNP']],
        sort_action = 'native',
        sort_mode = 'single',
        row_selectable = 'single',
        page_action = 'native',
        page_current = 0,
        page_size = 6,
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
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('rows')
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
        variant = ref + '>' + alt
        homs = mutation['hom']
        hets = mutation['het']
        try:
            impact = mutation['impact']
        except:
            impact = ''
        lines.append([coordinate, variant, homs, hets, impact, dbSNP])
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
    [Output('table_div', 'children'),
     Output('n_click_track', 'data'),
     Output('intro', 'style'),
     Output('variantNumber', 'data'),
     Output('coordinates', 'value'),
     Output('location', 'search'),
     Output('tableData','data')],
    [Input('search_button', 'n_clicks'),
     Input('coordinates_value','data'),
     Input('reference_genome', 'data'),
     Input('n_click_track', 'data'),
     Input('minQual', 'data'),
     Input('minCoverage', 'data'),
     Input('location', 'search'),
     ]
)
def getAPI(n_clicks, coordinates, referenceGenome, search_button_n_clicks, minQual, minCoverage, query):
    inputUpdate = dash.no_update
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
        chromosome = coordinates.split(':')[0]
        pos = coordinates.split(':')[1]
        start, end = int(pos.split('-')[0]), int(pos.split('-')[1])
        try: #if end - start > -1:
            query = 'http://geniepool-env-1.eba-ih62my9c.us-east-1.elasticbeanstalk.com/rest/index/' + referenceGenome + '/' + coordinates        
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
        data = df.apply(lambda x : listVariants(chromosome, x['pos'], x['entries']), axis = 1).tolist()
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
        df = pd.DataFrame(lines, columns = ['Coordinate', 'Variant', 'Homozygote Samples', 'Heterozygote Samples', 'Impact', 'dbSNP'])         
        df['Homozygotes'] = df['Homozygote Samples'].str.len()
        df['Heterozygotes'] = df['Heterozygote Samples'].str.len()
        ddt = generateDataTable(df)
        info = html.Div(id = 'info', style = info_style)
        csv_report = df.fillna('').to_csv(na_rep = '', index = False).replace(',nan,', ',,').replace('[','').replace(']','').replace("'",'')
        download_href = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_report)
        download_image = html.A('⬇️', href = download_href, download = 'GeniePool.csv', title = 'Download table', style = {'text-decoration' : 'none', 'fontSize' : '150%', 'float' : 'right', 'marginTop' : 1})
        samples = [i for i in df['Homozygote Samples'] if len(i) > 0] + [i for i in df['Heterozygote Samples'] if len(i) > 0]
        attributes = getAttributes(samples)
        explanation = 'Only variants with at least one sample, having at least one selected attribute, will remain.'
        phenoPicker = html.Div(
            dcc.Dropdown(
                id = 'phenoPicker',
                options = [{'label': v, 'value': v} for v in sorted(attributes, reverse = True)],
                multi = True,
                placeholder = 'Select attribute\s ℹ️',
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
        result = [phenoPicker, ddt, download_image, info]
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
        ucscA = html.A('UCSC', href = ucsc_link, target = '_blank', style = link_style)
        if referenceGenome == 'hg38':
            gnomAD_Url = 'https://gnomad.broadinstitute.org/variant/' + coordinates.replace(':','-') + mutation.replace('>','-') + '?dataset=gnomad_r3'                          
        else:
            gnomAD_Url = 'https://gnomad.broadinstitute.org/variant/' + coordinates.replace(':','-') + mutation.replace('>','-') + '?dataset=gnomad_r2_1' 
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
    server.run(debug=False)
