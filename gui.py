__version__ = "1"
app_name = "GPT Référent"


# BOILERPLATE

import streamlit as st
st.set_page_config(layout='centered', page_title=f'{app_name} {__version__}')
ss = st.session_state
if 'debug' not in ss: ss['debug'] = {}
import css
st.write(f'<style>{css.v1}</style>', unsafe_allow_html=True)
header1 = st.empty() # for errors / messages
header2 = st.empty() # for errors / messages
header3 = st.empty() # for errors / messages

st.title("MON EXPERT CGI Finance")
st.sidebar.header("Comment ça marche ? ")
st.sidebar.info("Interrogez l'expert derrière un document de référence en posant une simple question" )

# IMPORTS
import prompts
import model
import storage
import feedback
import cache
import os

from time import time as now

# HANDLERS

def on_api_key_change():
	api_key = ss.get('api_key') or os.getenv('OPENAI_KEY')	
	ss['api_key'] = api_key
	model.use_key(api_key) # TODO: empty api_key
	#
	if 'data_dict' not in ss: ss['data_dict'] = {} # used only with DictStorage
	ss['storage'] = storage.get_storage(api_key, data_dict=ss['data_dict'])
	ss['cache'] = cache.get_cache()
	ss['user'] = ss['storage'].folder # TODO: refactor user 'calculation' from get_storage
	model.set_user(ss['user'])
	ss['feedback'] = feedback.get_feedback_adapter(ss['user'])
	ss['feedback_score'] = ss['feedback'].get_score()
	#
	ss['debug']['storage.folder'] = ss['storage'].folder
	ss['debug']['storage.class'] = ss['storage'].__class__.__name__


# ss['community_user'] = os.getenv('COMMUNITY_USER')
# if 'user' not in ss and ss['community_user']:
on_api_key_change() # use community key

# COMPONENTS

def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(http://placekitten.com/200/200);
                background-repeat: no-repeat;
                padding-top: 120px;
                background-position: 20px 20px;
            }
            [data-testid="stSidebarNav"]::before {
                content: "My Company Name";
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 100px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )




def ui_spacer(n=2, line=False, next_n=0):
	for _ in range(n):
		st.write('')
	if line:
		st.tabs([' '])
	for _ in range(next_n):
		st.write('')

def ui_info():
	st.markdown(f"""
	# Super assistant
	version {__version__}
	
	Projet Mon super assistant
	""")
	ui_spacer(1)
	ui_spacer(1)
	ui_spacer(1)

def ui_api_key():
	if ss['community_user']:
		st.write('## 1. Optional - enter your OpenAI API key')
		t1,t2 = st.tabs(['community version','enter your own API key'])
		with t1:
			pct = model.community_tokens_available_pct()
			st.write(f'Community tokens available: :{"green" if pct else "red"}[{int(pct)}%]')
			st.progress(pct/100)
			st.write('Refresh in: ' + model.community_tokens_refresh_in())
			st.write('You can sign up to OpenAI and/or create your API key [here](https://platform.openai.com/account/api-keys)')
			ss['community_pct'] = pct
			ss['debug']['community_pct'] = pct
		with t2:
			st.text_input('OpenAI API key', type='password', key='api_key', on_change=on_api_key_change, label_visibility="collapsed")
	else:
		st.write('## 1. Enter your OpenAI API key')
		st.text_input('OpenAI API key', type='password', key='api_key', on_change=on_api_key_change, label_visibility="collapsed")

def index_pdf_file():
	if ss['pdf_file']:
		ss['filename'] = ss['pdf_file'].name
		if ss['filename'] != ss.get('fielname_done'): # UGLY
			with st.spinner(f'indexing {ss["filename"]}'):
				index = model.index_file(ss['pdf_file'], ss['filename'], fix_text=ss['fix_text'], frag_size=ss['frag_size'], cache=ss['cache'])
				ss['index'] = index
				debug_index()
				ss['filename_done'] = ss['filename'] # UGLY

def debug_index():
	index = ss['index']
	d = {}
	d['hash'] = index['hash']
	d['frag_size'] = index['frag_size']
	d['n_pages'] = len(index['pages'])
	d['n_texts'] = len(index['texts'])
	d['summary'] = index['summary']
	d['pages'] = index['pages']
	d['texts'] = index['texts']
	d['time'] = index.get('time',{})
	ss['debug']['index'] = d

def ui_pdf_file():
	st.write('## 1. Uploadez un nouveau document :')	
	disabled = not ss.get("api_key")
	t1,t2 = st.tabs(['Sélectionner', 'Charger'])	
	with t1:
		filenames = ['']
		if ss.get('storage'):
			filenames = ss['storage'].list()
			if ss.get('index') == None and len(filenames) > 0:
				name =  filenames[0]
				index = ss['storage'].get(name)
				ss['filename'] = name # XXX
				ss['index'] = index
		def on_change():
			name = ss['selected_file']
			if name and ss.get('storage'):
				with ss['spin_select_file']:
					with st.spinner('loading index'):
						t0 = now()
						index = ss['storage'].get(name)
						ss['debug']['storage_get_time'] = now()-t0
				ss['filename'] = name # XXX
				ss['index'] = index
			else:
				pass
		st.selectbox('select file', filenames, on_change=on_change, key='selected_file', label_visibility="collapsed", disabled=disabled)
		b_delete()
		ss['spin_select_file'] = st.empty()	
	with t2:
		st.file_uploader('pdf file', type='pdf', key='pdf_file', disabled=disabled, on_change=index_pdf_file, label_visibility="collapsed")
		b_save()

def ui_show_debug():
	st.checkbox('show debug section', key='show_debug')

def ui_fix_text():
	st.checkbox('fix common PDF problems', value=True, key='fix_text')

def ui_temperature():
	#st.slider('temperature', 0.0, 1.0, 0.0, 0.1, key='temperature', format='%0.1f')
	ss['temperature'] = 0.0

def ui_fragments():
	#st.number_input('fragment size', 0,2000,200, step=100, key='frag_size')
	st.selectbox('fragment size (characters)', [0,200,300,400,500,600,700,800,900,1000], index=3, key='frag_size')
	b_reindex()
	st.number_input('max fragments', 1, 10, 4, key='max_frags')
	st.number_input('fragments before', 0, 3, 1, key='n_frag_before') # TODO: pass to model
	st.number_input('fragments after',  0, 3, 1, key='n_frag_after')  # TODO: pass to model

def ui_model():
	models = ['gpt-3.5-turbo','gpt-4','text-curie-001']
	st.selectbox('main model', models, key='model', disabled=not ss.get('api_key'))
	st.selectbox('embedding model', ['text-em bedding-ada-002'], key='model_embed') # FOR FUTURE USE

def ui_hyde():
	st.checkbox('use HyDE', value=True, key='use_hyde')

def ui_hyde_summary():
	st.checkbox('use summary in HyDE', value=True, key='use_hyde_summary')

def ui_task_template():
	st.selectbox('task prompt template', prompts.TASK.keys(), key='task_name')

def ui_task():
	x = ss['task_name']
	st.text_area('task prompt', prompts.TASK[x], key='task')

def ui_hyde_prompt():
	st.text_area('HyDE prompt', prompts.HYDE, key='hyde_prompt')

def ui_question():
	st.write('## 2. Posez une question à ce document :')
	disabled = not ss.get('api_key')
	st.text_area('question', key='question', height=100, placeholder='Saisissez votre question ici', help='', label_visibility="collapsed", disabled=disabled)

# REF: Hypotetical Document Embeddings
def ui_hyde_answer():
	# TODO: enter or generate
	pass

def ui_output():
	output = ss.get('output','')
	st.markdown(output)

def ui_debug():
	if ss.get('show_debug'):
		st.write('### debug')
		st.write(ss.get('debug',{}))


def b_ask():
	c1,c2,c3,c4,c5 = st.columns([2,1,1,2,2])	
	if c1.button('Obtenez la réponse', disabled=False, type='primary', use_container_width=True):
		question = ss.get('question','')
		temperature = ss.get('temperature', 0.0)
		hyde = ss.get('use_hyde')
		hyde_prompt = ss.get('hyde_prompt')
		if ss.get('use_hyde_summary'):
			summary = ss['index']['summary']
			hyde_prompt += f" Context: {summary}\n\n"
		task = ss.get('task')
		max_frags = ss.get('max_frags',1)
		n_before = ss.get('n_frag_before',0)
		n_after  = ss.get('n_frag_after',0)
		index = ss.get('index',{})
		with st.spinner('preparing answer'):
			resp = model.query(question, index,
					task=task,
					temperature=temperature,
					hyde=hyde,
					hyde_prompt=hyde_prompt,
					max_frags=max_frags,
					limit=max_frags+2,
					n_before=n_before,
					n_after=n_after,
					model=ss['model'],
				)
		usage = resp.get('usage',{})
		usage['cnt'] = 1
		ss['debug']['model.query.resp'] = resp
		ss['debug']['resp.usage'] = usage
		ss['debug']['model.vector_query_time'] = resp['vector_query_time']
		
		q = question.strip()
		a = resp['text'].strip()
		ss['answer'] = a
		output_add(q,a)
		st.experimental_rerun() # to enable the feedback buttons

def b_clear():
	if st.button('clear output'):
		ss['output'] = ''

def b_reindex():
	if st.button('reindex'):
		index_pdf_file()

def b_reload():
	if st.button('reload prompts'):
		import importlib
		importlib.reload(prompts)

def b_save():
	db = ss.get('storage')
	index = ss.get('index')
	name = ss.get('filename')
	api_key = ss.get('api_key')
	disabled = not api_key or not db or not index or not name
	help = "The file will be stored for about 90 days. Available only when using your own API key."
	if st.button('Enregistrer le document', disabled=disabled, help=help):
		with st.spinner('Enregistrement du document en cours...'):
			db.put(name, index)

def b_delete():
	db = ss.get('storage')
	name = ss.get('selected_file')
	# TODO: confirm delete
	if st.button('Supprimer le document', disabled=not db or not name):
		with st.spinner('Suppression du document en cours...'):
			db.delete(name)
		st.experimental_rerun()

def output_add(q,a):
	if 'output' not in ss: ss['output'] = ''
	q = q.replace('$',r'\$')
	a = a.replace('$',r'\$')
	new = f'#### {q}\n{a}\n\n'
	ss['output'] = new + ss['output']

# LAYOUT

with st.sidebar:
	ui_info()
	ui_spacer(2)
	if os.getenv('ADVANCED_USER'):
		with st.expander('advanced'):
			ui_show_debug()
			b_clear()
			ui_model()
			ui_fragments()
			ui_fix_text()
			ui_hyde()
			ui_hyde_summary()
			ui_temperature()
			b_reload()
			ui_task_template()
			ui_task()
			ui_hyde_prompt()
	else:
		ss['model'] = 'gpt-3.5-turbo'
		ss['fix_text'] = True
		ss['frag_size'] = 400

add_logo()
#ui_api_key()
ui_pdf_file()
ui_question()
ui_hyde_answer()
b_ask()
ui_output()
ui_debug()
