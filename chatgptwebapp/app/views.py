"""
Definition of views.
"""

import os
import json
import sys
import openai
import logging
import tiktoken
import logging
from typing import Dict, List, cast
from django.shortcuts import render
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from opencensus.ext.azure.log_exporter import AzureLogHandler
from langchain.utilities import BingSearchAPIWrapper
from sequences import get_next_value
from datetime import datetime, timezone, timedelta
from concurrent import futures

from .models import * 
from .forms import UploadFileForm,UploadFileFormForCodeInterpriter,UploadFileFormForCodeInterpriterWithoutFile
from .types import *
from .decorators import login_required_conditional

## demo mode ##
demo_mode = os.getenv("DEMO_MODE_ENABLED")

### Application Insight ###
appInsightEnabled = os.getenv("APPINSIGHT_ENABLED")
appInsightEnabled = str(appInsightEnabled)
appInsightKey = os.getenv("APPINSIGHT_KEY")
appInsightKey = str(appInsightKey)

## Azure Openai api
azure_api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_api_base = str(azure_api_base)
azure_api_version = str(azure_api_version)
azure_api_key = str(azure_api_key)

## Openai api
# openai_api_base = os.getenv("OPENAI_ENDPOINT")
# openai_api_version = None
# openai_api_key = os.getenv("OPENAI_API_KEY")
# openai_api_base = str(openai_api_base)
# openai_api_key = str(openai_api_key)

## Azure Blob Storage for Code Interpriter
azure_blob_account_key = os.getenv("AZURE_BLOB_STORAGE_ACCOUNT_KEY")
azure_blob_account_name = os.getenv("AZURE_BLOB_STORAGE_ACCOUNT_NAME")
azure_blob_account_key = str(azure_blob_account_key)
azure_blob_account_name = str(azure_blob_account_name)

azure_blob_account_url:str = f"https://{azure_blob_account_name}.blob.core.windows.net"
azure_blob_connect_str:str = f'DefaultEndpointsProtocol=https;AccountName={azure_blob_account_name};AccountKey={azure_blob_account_key};EndpointSuffix=core.windows.net'

azure_blob_container_for_pdfupload = os.getenv("AZURE_BLOB_CONTAINER_NAME_FOR_PDFUPLOAD")
azure_blob_container_for_codeinterpreter = os.getenv("AZURE_BLOB_CONTAINER_NAME_FOR_CODEINTERPRETER")
azure_blob_container_for_csvpreset = os.getenv("AZURE_BLOB_CONTAINER_NAME_FOR_CSVPRESET")
azure_blob_container_for_pdfupload = str(azure_blob_container_for_pdfupload)
azure_blob_container_for_codeinterpreter = str(azure_blob_container_for_codeinterpreter)
azure_blob_container_for_csvpreset = str(azure_blob_container_for_csvpreset)

## Bing Search APIAZURE_BING_SEARCH_URL
bing_search_url = os.getenv("AZURE_BING_SEARCH_URL")
bing_subscription_key = os.getenv("AZURE_BING_SEARCH_API_KEY")
bing_search_url = str(bing_search_url)
bing_subscription_key = str(bing_subscription_key)

### Main ###
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if appInsightEnabled == "True":
    logger.addHandler(AzureLogHandler(connection_string=appInsightKey))

@login_required_conditional
@csrf_exempt
def chatui(request: HttpRequest):
    
    ### Application Insight ###
    logger.info('[Access log]chatui page')

    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/chatui.html',
        {
            'title':'Expert Imitator',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )

@csrf_exempt
def chat(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        return HttpResponse("data:Error:デモモードではこの機能は利用できません。|E|".encode(), content_type='text/event-stream')
    else:
        print("Called "+ thisFunctionName)
    
    if request.user.is_authenticated:
        # 認証されたユーザーの処理
        username = request.user.username # type: ignore
        print("認証されたユーザー:" + username)
        pass
    else:
        # 認証されていないユーザーの処理
        print("認証されていないユーザー")
        pass
    
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key
    
    para = ""
    searchflg = ""
    sessionid = ""
    pageid = "" 
    if request.method == 'GET':
        if 'p' in request.GET:
            para = request.GET['p']
                    
    if request.method == 'POST':
        # JSON文字列
        datas = json.loads(request.body)
 
        # requestには、param1,param2の変数がpostされたものとする
        para = datas["p"]
        searchflg = datas["search"]
        pageid = datas["pageid"]
        sessionid = datas["sessionid"]
    print(pageid)
    print(sessionid)

    if para == "":
        para = "[{'role': 'user', 'content': '富士山と同じ高さの山はどこですか？5つ挙げてください。\n'}]",

    messagesTemp = [
            {"role": "system", "content":"You are ChatGPT, a large language model trained by OpenAI. Follow the user's instructions carefully. Respond using markdown.Use emojis sometimes too."},
            ]
    
    for i in para:
        messagesTemp.append(
            {"role": i['role'], "content":i['content']}, # type: ignore
        )


    last_user_query = messagesTemp[-1]['content']  # 最後の値を取得

    response = ""
    try:
        search_auto_neccesary_flg = ""
        search_exe_flg = False
        if searchflg == "auto":
            # search_auto_neccesary_flg = search_neccesary_check(last_user_query)
            # if "Yes" in search_auto_neccesary_flg:
            search_exe_flg = True
        elif searchflg == "on":
            search_exe_flg = True
        elif searchflg == "off":
            search_exe_flg = False
                
        if search_exe_flg:

            search = BingSearchAPIWrapper(bing_search_url=bing_search_url, bing_subscription_key=bing_subscription_key,k=50)
            
            # 'content'が'user'のものだけを取り出して結合する
            user_query = ''.join([message['content'] for message in messagesTemp if message['role'] == 'user'])

            print(user_query)
            
            keywordforsearch = get_keyword_forsearch(user_query)

            if keywordforsearch != "unnecessary":
                searchResult = search.run(keywordforsearch)

                contexts:str = 'Content: ' + searchResult
                
                # systemメッセージの入れ替え
                del messagesTemp[0]  # 最初の要素を削除            
                messagesTemp.insert(0, 
                {"role":"system","content":'You are a chatbot having a conversation with a human.\n\
                Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").\n\
                Please answer in Japanese.Respond using markdown.Use emojis sometimes too.\n\
                \n\
                ' + contexts + '\n\
                '}
                )
                                    

            logger.info('[Chat Bing+] '+ last_user_query[0:1000] )

        else:
            logger.info('[Chat Query] '+ messagesTemp[-1]['content'][0:1000] )
            
        # token size check
        output_max_token_size:int = 4000
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokenized = tokenizer.encode(str(messagesTemp))
        
        # 回答用のトークンサイズ2000を考慮し、クエリ用トークンサイズが2000を超えたら、16kモデルを使う turboは4096が上限。16kは16385が上限
        enginetype = "gpt-4"
        if((len(tokenized)+output_max_token_size) > 30000):
            errorMessage = "入力文字数が上限を超えています。"
            logger.exception('['+thisFunctionName+']Error:' + errorMessage )
            return HttpResponse("data:Error:"  + errorMessage + str("|E|".encode()), content_type='text/event-stream')
        elif((len(tokenized)+output_max_token_size) > 6000):
            enginetype = "gpt-4-32k"
        
        # Define a generator function to stream the response
        def generate_response():
            # yield 'start\n' # 最初のデータ

            for chunk in openai.ChatCompletion.create(
                engine=enginetype,
                messages=messagesTemp,
                temperature=0.8,
                max_tokens=output_max_token_size, # 回答用のトークン数。このサイズを考慮して文字数上限チェックがされる
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=True,
            ):
                if len(chunk["choices"]) != 0: # type: ignore                    
                    content = chunk["choices"][0].get("delta", {}).get("content") # type: ignore
                    if content is not None:
                        yield "data:" + content.replace('\n', '@n@').replace(' ', '@s@') + "\n\n"
            yield "data:|E|".encode() # 最後のデータ

        # Return a streaming response to the client
        response = StreamingHttpResponse(generate_response(), content_type='text/event-stream')
    except Exception as e:
        errorMessage = str(e.args[0])
        logger.exception('['+thisFunctionName+']Error:' + errorMessage )
        # response = errorMessage
        response = HttpResponse("data:Error:"  + errorMessage + str("|E|".encode()), content_type='text/event-stream')

    return response

def search_neccesary_check(query):
    
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key
    
    messagesTemp = [
    {"role": "system", "content":"You are ChatGPT, a large language model trained by OpenAI. Follow the user's instructions carefully."},
    {"role": "user", "content":'Answer Yes or No if additional information is required to answer the following questions.Answer Yes or No only.\n""""'+query+'"""""'},
    ]
        
    res = openai.ChatCompletion.create(
            engine="gpt-4",
            messages=messagesTemp,
            temperature=1,
            max_tokens=30,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            # stream=True,
        )

    result = res.choices[0]["message"]["content"].strip() # type: ignore
    return result

def get_keyword_forsearch(query):
    
    # APIキーの設定
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key

    # AIが使うことができる関数を羅列する
    functions = [
        # AIが、質問に対してこの関数を使うかどうか、
        # また使う時の引数は何にするかを判断するための情報を与える
        {
            "name": "search_the_web",
            "description": "検索エンジンに問い合わせて、Webの最新の情報を取得する。",
            "parameters": {
                "type": "object",
                "properties": {
                    # keywords引数の情報
                    "query": {
                        "type": "string",
                        "description": "検索エンジンに問い合わせるために最適なカンマ区切りのキーワードクエリ。重要なキーワードから順番に羅列し、最大10キーワードまでとする。例: 日本で歴代最長の首相は誰？を聞きたい場合、「歴代最長,首相,日本」となる。",
                    },
                },
                "required": ["query"],
            },
        }
    ]

    # 1段階目の処理
    # AIが質問に対して使う関数と、その時に必要な引数を決める
    # 特に関数を使う必要がなければ普通に質問に回答する
    response = openai.ChatCompletion.create(
        engine="gpt-4",
        messages=[
            {"role": "user", "content": query},
        ],
        functions=functions,
        function_call="auto",
    )
    message = response["choices"][0]["message"] # type: ignore
        
    res:str = ""
    if message.get("function_call"):
        # 関数を使用すると判断された場合

        # 使うと判断された関数名
        function_name = message["function_call"]["name"]
        # その時の引数dict
        arguments = json.loads(message["function_call"]["arguments"])
        
        res = arguments.get("query")
    else:
        res = "unnecessary"

    print(res)    
    return res

@csrf_exempt
def getid(request: HttpRequest):
    
    idname = ""
    seq_id_name = 0
    if request.method == 'GET':
        if 'id_name' in request.GET:
            idname = request.GET['id_name']
            
    if idname != "":
        seq_id_name = get_next_value(idname)
        
    res = {
        'id':seq_id_name
    }
    #json形式の文字列を生成
    json_str = json.dumps(res, ensure_ascii=False, indent=2) 
    return HttpResponse(json_str)

@csrf_exempt
def conv_save2db(request: HttpRequest):
      
    usermessages:str = ""
    sessionid:int = 0
    pageid:str = ""
    userid:str = request.user.username # type: ignore
    if request.method == 'POST':
        # JSON文字列
        datas = json.loads(request.body)
 
        # requestには、param1,param2の変数がpostされたものとする
        usermessages = datas["p"]
        pageid = datas["pageid"]       
        sessionid = datas["sessionid"]
    # print(pageid)
    # print(sessionid)
    
    allmessages = [
        {"role": "system", "content":"You are ChatGPT, a large language model trained by OpenAI. Follow the user's instructions carefully. Respond using markdown.Use emojis sometimes too."},
        ]

    for i in usermessages:
        # DBに格納できる最大数を超えた場合は切り捨てる
        # alllength = sum(len(s) for s in allmessages)        
        nowlength = len(json.dumps(allmessages, ensure_ascii=False, indent=2))
        newlength = len(json.dumps(i['content'], ensure_ascii=False, indent=2)) # type: ignore
        alllength = nowlength + newlength
        print("content size:" + str(alllength))

        # 19000文字を超えた場合は切り捨てる        
        if alllength > 19000:
            # 19000文字を超えてない場合は、500文字までセットする
            if nowlength < 19000:
                allmessages.append(
                    {"role": i['role'], "content":i['content'][1:500] + "【超過により文末切捨】"}, # type: ignore
                )
        else:
            allmessages.append(
                {"role": i['role'], "content":i['content']}, # type: ignore
            )
    
    # 会話履歴をDBに保存
    ChatHistoryModel.objects.update_or_create(
        id=sessionid, 
        defaults={'userid':userid,
                'functionid':pageid,
                'content':allmessages,
                'timestamp':datetime.now(pytz.timezone('Asia/Tokyo'))})
    return HttpResponse("OK")

# langchainを使わずに、Searchを使って最新情報を反映させる関数
@csrf_exempt
def documentsearch(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        return HttpResponse("data:Error:デモモードではこの機能は利用できません。|E|".encode(), content_type='text/event-stream')
    else:
        print("Called "+ thisFunctionName)
    
    if request.user.is_authenticated:
        # 認証されたユーザーの処理
        username = request.user.username # type: ignore
        print("認証されたユーザー:" + username)
        pass
    else:
        # 認証されていないユーザーの処理
        print("認証されていないユーザー")
        pass
    
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key
    
    para:str = ""
    pageid:str = ""
    sessionid:str = ""
    filenames: List[str] = []
    
    if request.method == 'POST':
        # JSON文字列
        datas = json.loads(request.body)
 
        # requestには、param1,param2の変数がpostされたものとする
        para = datas["p"]
        pageid = datas["pageid"]
        sessionid = datas["sessionid"]
        filenames = datas["select_option_list"] 

    print(pageid)
    print(sessionid)

    if para == "":
        errorMessage = "必要なパラメータがありません。"
        return errorMessage

    user_query = para[-1]['content']  # 最後の値を取得 # type: ignore
    
    logger.info('[Search pdf:] '+ user_query[0:1000] )
    
    response = ""
    try:                
        logger.info('[Document Search] '+ para[-1]['content'][0:1000] ) # type: ignore
            
        embres = openai.Embedding.create(
            input=user_query,
            engine="text-embedding-ada-002"
            )
        queryvectordata = embres['data'][0]['embedding'] # type: ignore
        
        filenamestr:str = ""

        # IN句のパラメータを動的に生成                
        placeholders = ', '.join(["'%s'"] * len(filenames))
        filenamestr = f"WHERE document_filename IN ({placeholders})"
        filenamestr = filenamestr % tuple(filenames)

        sqlquery = f"SELECT id,document_filename,page_no,origntext,create_timestamp,distance FROM (SELECT *, embedding <-> '%s' AS distance FROM public.app_documentvectordatamodel {filenamestr}) AS A WHERE distance < %s ORDER BY distance Limit %s"
            
        val1:str =str(queryvectordata); # embedding
        val2:str =str("0.7"); # distance
        val3:str =str("20"); # limit count

        sqlquery = sqlquery % (val1,val2,val3)

        rows_counter:int = 1
        contexts:str = ''
        for p in DocumentVectorDataModel.objects.raw(sqlquery):
            
            documentsasurl:str = get_sasurl_filenameonly(p.document_filename)
            
            context:str = 'Content: ' + p.origntext 
            context += ' Source: [資料名] '+ p.document_filename + ' [URL] (' + documentsasurl + ') [ページ番号] ' + p.page_no
            
            context_temp:str = contexts + context + '\n'
            # token size check
            tokenizer = tiktoken.get_encoding("cl100k_base")
            tokenized = tokenizer.encode(context_temp)
            
            if(len(tokenized) > 10000):
                break
            else:
                contexts = context_temp

            # print(p.origntext)
            print('filename:' + p.document_filename +' page:' + p.page_no +' distance:' + str(p.distance) +' token size:' + str(len(tokenized))+' page count:' + str(rows_counter))
            # print('page:' + p.origntext)
            rows_counter += 1

        if(len(contexts) != 0):

            messagesTemp = [
            {"role":"system","content":'You are a chatbot having a conversation with a human.\n\
            Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").\n\
            If you don\'t know the answer, just say that you don\'t know. Don\'t try to make up an answer.\n\
            ALWAYS return a "SOURCES" part in your answer.Respond using markdown.Use emojis sometimes too.\n\
            \n\
            ' + contexts + '\n\
            '}
            ]
                        
            for i in para:
                messagesTemp.append(
                    {"role": i['role'], "content":i['content']}, # type: ignore
                )
        
            # 最後の要素を削除
            last_element = messagesTemp.pop()
            last_user_query = user_query + "可能な限り箇条書きや表を利用して、わかりやすい表現で説明してください。また読みやすい用に１つ１つの文章は長すぎず、リズムの良い文章にしてください。回答文の最後に参照元情報（資料名,URL,ページ番号）を纏めて必ず付与してください。"
            
            messagesTemp.append(
                {"role":"user","content":last_user_query}  
            )

            # # トークンサイズのカウント
            # tokenizer = tiktoken.get_encoding("cl100k_base")
            # temptext = str(messagesTemp)
            # tokenized = tokenizer.encode(temptext)
            # print("Token Length:{}".format(len(tokenized)))

            # Define a generator function to stream the response
            def generate_response():

                for chunk in openai.ChatCompletion.create(
                    engine="gpt-4-32k",
                    messages=messagesTemp,
                    temperature=0.9,
                    max_tokens=2000,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=True,
                ):
                    if len(chunk["choices"]) != 0: # type: ignore                    
                        content = chunk["choices"][0].get("delta", {}).get("content") # type: ignore
                        if content is not None:
                            yield "data:" + content.replace('\n', '@n@').replace(' ', '@s@') + "\n\n"
                yield "data:|E|".encode() # 最後のデータ

            # Return a streaming response to the client
            response = StreamingHttpResponse(generate_response(), content_type='text/event-stream')

        else:
            response = HttpResponse("data:資料内を探しましたが、質問の回答に適切な情報は見つかりませんでした。|E|".encode(), content_type='text/event-stream')
            # return errorMessage

    except Exception as e:
        errorMessage = str(e.args[0])
        logger.exception('['+thisFunctionName+']Error:' + errorMessage )
        response = HttpResponse("data:Error:" + errorMessage + str("|E|".encode()), content_type='text/event-stream')
        # response = errorMessage
    
    return response

@csrf_exempt
def getlist_of_registered_document(request: HttpRequest):

    # if request.method == 'GET':
        # if 'id_name' in request.GET:
        #     idname = request.GET['id_name']

    JST = timezone(timedelta(hours=+9), 'JST')

    res = []
    sqlquery:str = "select document_filename,document_name,total_page_no,discription,document_url,create_timestamp from public.app_documentfilenamevectordata order by create_timestamp desc"
    for p in DocumentFileNameVectorData.objects.raw(sqlquery):                    

        document_url:str = get_sasurl(p.document_filename,p.document_url)
        jst_time = p.create_timestamp.replace(tzinfo=timezone.utc).astimezone(JST)
        jst_datetime = jst_time.strftime("%Y/%m/%d %H:%M:%S")
        documentlist = {
            'document_filename':p.document_filename,
            'document_name':p.document_name,
            'total_page_no':p.total_page_no,
            'discription':p.discription,
            'document_url':document_url,
            'create_timestamp':jst_datetime,
        }
        res.append(documentlist)
            
    #json形式の文字列を生成
    json_str = json.dumps(res, ensure_ascii=False, indent=2) 
    return HttpResponse(json_str)

from io import BytesIO
@csrf_exempt
def document_upload_save(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        return HttpResponse(json.dumps({ "status": "Error:デモモードではこの機能は利用できません。", "data":[]}, ensure_ascii=False, indent=2))
    else:
        print("Called "+ thisFunctionName)
        
    # 保存するBlobのコンテナ名
    container_name:str = azure_blob_container_for_pdfupload
    
    res:type_res_document_upload_save = {"status":"","data":[]}
    
    if request.method == 'POST':
        try:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                sys.stderr.write("*** file_upload *** \n")
                document_name:str = request.POST['document_name']
                description:str = request.POST['description']
                file_obj = request.FILES['file']
                sys.stderr.write(file_obj.name + "\n")
                
                logger.info('[Regist pdf:] '+ file_obj.name )
               
                res1:type_res_document_upload_save = pdf_read_uploaded_file(file_obj, document_name, description,container_name)
                restemp:str = "PDF Read " + res1["status"] + "\n"

                if res1["status"] == "OK":
                    # Uploadされたデータをファイル出力
                    res2:str = handle_uploaded_file(file_obj,file_obj.name,container_name)
                    restemp += "PDF Save " + res2 + "\n"
                
                res = res1
                
            else:
                sys.stderr.write("*** file_upload *** \n")
                sys.stderr.write("Error:" + str(form.errors)+"\n")
                res = { "status": "NG " + str(form.errors), "data":[] }
        except Exception as e:
            sys.stderr.write("*** file_upload *** \n")
            sys.stderr.write(str(e) + "\n")
            logger.exception('['+thisFunctionName+']Error:' + str(e) )
            res = { "status": "NG " + str(e) , "data":[]}
        #json形式の文字列を生成
    json_str:str = json.dumps(res, ensure_ascii=False, indent=2) 
    return HttpResponse(json_str)

# ------------------------------------------------------------------
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

def handle_uploaded_file(file_obj,file_name:str,container_name:str)->str:
    
    try:
        # Blobにもアップロードする    
        # Azure Blob Storageの接続文字列を取得する
        connect_str = azure_blob_connect_str

        # BlobServiceClientオブジェクトを作成する
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        # Blob名を指定してBlobClientオブジェクトを作成する
        blob_name = file_name
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # ファイルをアップロードする
        with file_obj.open() as f:
            blob_client.upload_blob(f, overwrite=True)

        return "OK"
    except Exception as e:
        sys.stderr.write("*** handle_uploaded_file *** \n")
        sys.stderr.write(str(e) + "\n")
        # return str(e)
        return "NG:" + str(e)
# ------------------------------------------------------------------

def handle_uploaded_file2(file_path:str,file_name:str,container_name:str)->str:
    
    try:
        # Blobにもアップロードする    
        # Azure Blob Storageの接続文字列を取得する
        connect_str = azure_blob_connect_str

        # BlobServiceClientオブジェクトを作成する
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        # Blobにアップロード
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return "OK"
    except Exception as e:
        sys.stderr.write("*** handle_uploaded_file *** aaa ***\n")
        sys.stderr.write(str(e) + "\n")
        # return str(e)
        return "NG:" + str(e)
# ------------------------------------------------------------------

# SAS URLを生成する関数
def get_sasurl_filenameonly(filename:str)->str:
 
    sqlquery:str = f"select document_filename,document_url from public.app_documentfilenamevectordata where document_filename = '{filename}'"
    sas_url:str = ""
    for p in DocumentFileNameVectorData.objects.raw(sqlquery):                    
        sas_url = get_sasurl(p.document_filename,p.document_url)
    return sas_url

def get_sasurl(document_filename:str,container_name:str)->str:
    
    try:
            
        sas_token=generate_blob_sas(
                account_key=azure_blob_account_key,# ストレージアカウントのキー
                account_name=azure_blob_account_name, # ストレージアカウントの名前
                container_name=container_name,# コンテナの名前
                blob_name=document_filename,# Blobの名前
                permission=BlobSasPermissions(read=True, write=False, delete=False, list=False),# アクセス権限
                expiry=datetime.utcnow() + timedelta(seconds=600)# トークンの有効期限
            )
        # SAS URLを生成
        sas_url=f"{azure_blob_account_url}/{container_name}/{document_filename}?{sas_token}"
        # print(sas_url)

        # SAS URLを返す
        return sas_url
    except Exception as e:
        # エラーが発生した場合、エラーメッセージを出力して"NG"を返す
        sys.stderr.write("*** get_sasurl ***\n")
        sys.stderr.write(str(e) + "\n")
        return "NG:" + str(e)
# ------------------------------------------------------------------

# 必要なPdfminer.sixモジュールのクラスをインポート
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from io import StringIO
import re

def pdf_read_uploaded_file(file_obj,document_name:str,description:str,container_name:str)->type_res_document_upload_save:

    try:
        # 標準組込み関数open()でモード指定をbinaryでFileオブジェクトを取得
        # fp = open(formUrl, 'rb')
        fp = BytesIO(file_obj.read())

        # 出力先をPythonコンソールするためにIOストリームを取得
        outfp = StringIO()

        # 各種テキスト抽出に必要なPdfminer.sixのオブジェクトを取得する処理
        rmgr = PDFResourceManager() # PDFResourceManagerオブジェクトの取得
        lprms = LAParams()          # LAParamsオブジェクトの取得
        device = TextConverter(rmgr, outfp, laparams=lprms)    # TextConverterオブジェクトの取得
        # device = TextConverter(rmgr, outfp, codec='utf-8', laparams=lprms)    # TextConverterオブジェクトの取得
        iprtr = PDFPageInterpreter(rmgr, device) # PDFPageInterpreterオブジェクトの取得
        
        outtexts:List[str] = []  # テキスト抽出結果を格納する変数
        # PDFファイルから1ページずつ解析(テキスト抽出)処理する
        for page in PDFPage.get_pages(fp):
            # ページの読み込み。outfpにテキスト抽出結果が格納される
            iprtr.process_page(page)
            outtexttemp:str = outfp.getvalue()

            ## 事前処理（無駄な文字を削ったりする)
            # 文字列のouttexttemp内の連続する空白文字を単一の空白文字に置き換え、両端の余分な空白を削除します。
            outtexttemp = re.sub(r'\s+',  ' ', outtexttemp).strip()
            # 三回以上連続する改行を二回に置き換えます。
            outtexttemp = re.sub(r'\n{3,}', '\n\n', outtexttemp)
            # 2回連続する改行は対象外とするが、1回の改行は対象とする場合は対象とするにはどう書けばいいですか？
            outtexttemp = re.sub(r'(?<!\n)\n(?!\n)', ' ', outtexttemp)
            # outtexttemp = re.sub(r". ,","",outtexttemp)
            # outtexttemp = outtexttemp.replace("..",".")
            # outtexttemp = outtexttemp.replace(". .",".")
            # outtexttemp = outtexttemp.replace("\n", "")
            # 文字列のouttexttempの両端にある余分な空白を削除します。
            outtexttemp = outtexttemp.replace('\x00', ' ')
            outtexttemp = outtexttemp.replace('<|endoftext|>', ' ')
            outtexttemp = outtexttemp.strip()
            
            outtexts.append(outtexttemp)
            # sys.stderr.write(outtexttemp + "\n")

            outfp.truncate(0)  # StringIOオブジェクトの中身をクリア
            outfp.seek(0)       # StringIOオブジェクトの先頭にシーク

        outfp.close()  # I/Oストリームを閉じる
        device.close() # TextConverterオブジェクトの解放

        outlines_res:Tuple[List[type_chapter_by_page],List[type_chapter_by_chapter]] = get_document_outline(fp)
        # outlineを取得する
        outlinetexts:List[type_chapter_by_page] = outlines_res[0]
        outlinetexts2:List[type_chapter_by_chapter] = outlines_res[1]

        fp.close()     #  Fileストリームを閉じる
        
        res:type_res_document_upload_save = {"status":"","data":[]}
        res_temp = make_vector_save_db(outtexts,document_name,description,file_obj.name,container_name,outlinetexts)
        if res_temp != "OK":
            return {"status":"NG"+ res_temp,"data":[]}
              
        return {"status":"OK","data" :outlinetexts2}
    except Exception as e:
        return  {"status":"NG"+ str(e),"data":[]}

import uuid
import pytz   
def make_vector_save_db(targetdata,document_name:str,description:str,filename:str,container_name:str,outlinetexts:List[type_chapter_by_page])->str:

    try:
        # 削除するレコードの条件を指定する
        condition = {
            'document_filename': filename,
        }

        # 明細テーブルからレコードを削除する
        DocumentVectorDataModel.objects.filter(**condition).delete()
        # ヘッダーテーブルからレコードを削除する
        DocumentFileNameVectorData.objects.filter(**condition).delete()

        # 並列処理でベクトル化を行う
        thread_count:int = 2 # 並列処理のスレッド数。高くし過ぎるとOpenAIのAPIの制限に引っかかるので注意
        future_result:str = "OK"
        future_list = []
        with futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            for pagecount in range(len(targetdata)):
                future = executor.submit(make_vector_save_db_thread, pagecount=pagecount, targetdata=targetdata, document_name=document_name, description=description, filename=filename, outlinetexts=outlinetexts )
                future_list.append(future)
            for future in futures.as_completed(fs=future_list):
                result = future.result()
                if result != "OK":
                    future_result = "NG:" + result

        if future_result == "OK":
            # 結果を処理する
            # 明細をベクトルデータをDBに保存
            DocumentFileNameVectorData.objects.update_or_create(
                document_filename = filename,
                document_name = document_name,
                total_page_no = len(targetdata),
                discription = description,
                document_url = container_name,
                create_timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
            )
        else:
            return "NG:make_vector_save_db_threadでerrorが発生しました。"

    except Exception as e:
        print("NG:" + str(e))
        return "NG:" + str(e)
    
    return "OK"

def make_vector_save_db_thread(pagecount:int,targetdata:List[str],document_name:str,description:str,filename:str, outlinetexts:List[type_chapter_by_page])->str:
    try:
        pagenumber:int = pagecount+1
        pagenumbers:str = "{}".format(pagenumber)
        content:str = targetdata[pagecount]

        # 目次がある場合はドキュメントの章番号・章の説明を取得
        chaptertitle:str = "unknown"
        for outline in outlinetexts:
            if outline["pageno"] == pagenumber:
                chaptertitle = outline["chapter_titles"]
                break

        # ドキュメント名・ドキュメントの説明・ページ番号・ドキュメント本文を先頭に加える
        embeddingcontent:str = "[document title] " + document_name + " [document discription] " + description + " [document page number] " + pagenumbers + " [document chapter title] " + chaptertitle +" [document body] " + content
        
        # 8192トークンを超える文字列のベクトル化はできないので、8192を上限にする
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokenized = tokenizer.encode(embeddingcontent)
        if len(tokenized) > 8192:
            embeddingcontent = tokenizer.decode(tokenized[:8192])

        vectordata:str = ""
        whilecount = 3
        while whilecount > 0:    
            vectordata = getembedding(embeddingcontent)
            # 正常の場合（NGという文字列を含んでいなかったら）、ループを抜ける
            if "NG:" not in vectordata:
                break
            whilecount -= 1 # 3回までリトライする
        
        # 明細をベクトルデータをDBに保存
        DocumentVectorDataModel.objects.update_or_create(
        id=str(uuid.uuid4()),
        document_filename = filename,
        page_no = pagenumbers,
        embedding = vectordata,
        embeddingtext = embeddingcontent,
        origntext = content,
        create_timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))  # 日本標準時を表すタイムゾーンオブジェクトを作成する
        )

        print("Page:" + str(pagenumbers) + " Tokensize:" + str(len(tokenized)) + " Content:" + content[0:100])

        
    except Exception as e:
        print("NG:" + str(e))
        return "NG:" + str(e)
    
    return "OK"

def getembedding(embeddingcontent:str)->str:
    
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key
    
    try:
        response = openai.Embedding.create(
        input=embeddingcontent,
        engine="text-embedding-ada-002"
        )
                
        vectordata = response['data'][0]['embedding'] # type: ignore
        return vectordata

    except Exception as e:
        print("NG:" + str(e))
        return "NG:" + str(e)


# ------------------------------------------------------------------
# ドキュメントの目次を取得する関数
from typing import Any, List, Union
from pdfminer.pdfdocument import PDFDocument,PDFNoOutlines
from pdfminer.pdftypes import PDFObjRef, resolve1 
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSLiteral

def get_document_outline(fp) -> Tuple[List[type_chapter_by_page],List[type_chapter_by_chapter]]:
    
    # PDFParserオブジェクトの取得
    parser = PDFParser(fp)

    # PDFDocumentオブジェクトの取得
    doc = PDFDocument(parser)
    
    # PDFのOutlinesのDestを分解する
    def resolve_dest(dest: object) -> Any:
        if isinstance(dest, (str, bytes)):
            dest = resolve1(doc.get_dest(dest))
        elif isinstance(dest, PSLiteral):
            dest = resolve1(doc.get_dest(dest.name))
        if isinstance(dest, dict):
            dest = dest["D"]
        if isinstance(dest, PDFObjRef):
            dest = dest.resolve()
        return dest

    ESC_PAT = re.compile(r'[\000-\037&<>()"\042\047\134\177-\377]')

    # 文字列からゴミを取り除く
    def escape(s: Union[str, bytes]) -> str:
        if isinstance(s, bytes):
            us = str(s, "latin-1")
        else:
            us = s
        return ESC_PAT.sub(lambda m: "&#%d;" % ord(m.group(0)), us)

    # ＜目次＞のテキストを抽出する
    try:
        outlines = doc.get_outlines() # get_outlines()メソッドはGeneraterを戻す
            
        # for outline in outlines:
        #     level = outline[0]    # 目次の階層を取得 <インデックス0>
        #     title = outline[1]    # 目次のコンテンツを取得 <インデックス1>
        #     dest = outline[2]    # 目次のリンク先を取得 <インデックス2>
        #     action = outline[3]    # 目次のアクションを取得 <インデックス3>
        #     se = outline[4]    # 目次のseを取得 <インデックス4>
        #     print(level,title,outline[2],outline[3],outline[4])

        pages = {
            page.pageid: pageno
            for (pageno, page) in enumerate(PDFPage.create_pages(doc), 1)
        }
        
        chapters_temp:List[type_chapter_per_page] = []
        
        for (level, title, dest, a, se) in outlines:
            pageno = None
            if dest:
                dest = resolve_dest(dest)
                pageno = pages[dest[0].objid]
            elif a:
                action = a
                if isinstance(action, dict):
                    subtype = action.get("S")
                    if subtype and repr(subtype) == "/'GoTo'" and action.get("D"):
                        dest = resolve_dest(action["D"])
                        pageno = pages[dest[0].objid]
            s = escape(title)
            if pageno is not None:
                chapters_temp.append({"pageno_start": pageno, "pageno_end": 0,"chapter_title": s, "level": level})
        
        # chapters_temp = sorted(chapters_temp, key=lambda x: x["pageno_start"],reverse=False)
        for (i,chapter_temp) in enumerate(chapters_temp):
            if i == len(chapters_temp)-1:
                chapters_temp[i]["pageno_end"] = len(pages)
            else:
                if chapters_temp[i]["pageno_start"] == chapters_temp[i+1]["pageno_start"]:
                    chapters_temp[i]["pageno_end"] = chapters_temp[i]["pageno_start"]
                else:
                    chapters_temp[i]["pageno_end"] = chapters_temp[i+1]["pageno_start"]-1

        chapters_bypage:List[type_chapter_by_page] = []
        chapters_bychapter:List[type_chapter_by_chapter] = []
        
        chapters_temp2:List[type_chapter_per_page2] = get_document_outline_convert(chapters_temp)

        for i in range(len(chapters_temp2)):
            chapters_bychapter.append({"pageno_start": chapters_temp2[i]["pageno_start"],"pageno_end": chapters_temp2[i]["pageno_end"],"chapter_title_all": chapters_temp2[i]["leveltext"],"leaf_flg": chapters_temp2[i]["leaf_flg"]})
            
        # 末端フラグがTrueのデータのみを抽出する
        chapters_temp2 = [chapter for chapter in chapters_temp2 if chapter['leaf_flg']]
        
        # 1からlen(pages)まで繰り返す
        for pageno in range(1, len(pages) + 1):
            # pagenoがchapterの開始ページと終了ページの間にあるかどうかを判定する
            chapter_titles_per_page = ""
            for chapter in chapters_temp2:
                if chapter["pageno_start"] <= pageno <= chapter["pageno_end"]:
                    if chapter_titles_per_page == "":
                        chapter_titles_per_page += chapter["leveltext"]
                    else:
                        chapter_titles_per_page += "," + chapter["leveltext"]
            
            if chapter_titles_per_page == "":
                chapter_titles_per_page = "unknown"
            
            chapters_bypage.append({'pageno': pageno, 'chapter_titles': chapter_titles_per_page})
                        
        return chapters_bypage,chapters_bychapter

    except PDFNoOutlines: # 目次がないPDFの場合のエラー処理対策
        # print("このコンテンツには目次はありません")
        return [],[]


def get_document_outline_convert(chapters_temp:List[type_chapter_per_page]) -> List[type_chapter_per_page2] :
   
    level1_cnt:int = 0
    level2_cnt:int = 0
    level3_cnt:int = 0
    level4_cnt:int = 0
    level5_cnt:int = 0
    level6_cnt:int = 0
    level1_currenttext:str = ""
    level2_currenttext:str = ""
    level3_currenttext:str = ""
    level4_currenttext:str = ""
    level5_currenttext:str = ""
    level6_currenttext:str = ""
        
    res:List[type_chapter_per_page2] = []
    pageno_start_last:int = 0
    for item in chapters_temp:
        temp:type_chapter_per_page2 = {"pageno_start":0,"pageno_end":0,"chapter_title":"","leaf_flg":False,"leveltext":"","level1":0,"level2":0,"level3":0,"level4":0,"level5":0,"level6":0}
        
        # ページが変わったら一つ前のデータの末端フラグをTrueにする
        if item["pageno_start"] != pageno_start_last and len(res) != 0:
            res[-1]["leaf_flg"] = True
        
        if item["level"] == 1:

            if level6_cnt != 0 or level5_cnt != 0 or level4_cnt != 0 or level3_cnt != 0 or level2_cnt != 0 or level1_cnt != 0:
                # 一つ前のデータの末端フラグをTrueにする
                res[-1]["leaf_flg"] = True

            level1_cnt += 1
            level1_currenttext = str(level1_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":False,"leveltext":leveltext,"level1":level1_cnt,"level2":0,"level3":0,"level4":0,"level5":0,"level6":0}
            level2_cnt = 0
            level3_cnt = 0
            level4_cnt = 0
            level5_cnt = 0
            level6_cnt = 0

        elif item["level"] == 2:

            if level6_cnt != 0 or level5_cnt != 0 or level4_cnt != 0 or level3_cnt != 0 or level2_cnt != 0:
                # 一つ前のデータの末端フラグをTrueにする
                res[-1]["leaf_flg"] = True

            level2_cnt += 1
            level2_currenttext = "/" + str(level1_cnt) + "-" + str(level2_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext + level2_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":False,"leveltext":leveltext,"level1":level1_cnt,"level2":level2_cnt,"level3":0,"level4":0,"level5":0,"level6":0}
            level3_cnt = 0
            level4_cnt = 0
            level5_cnt = 0
            level6_cnt = 0

        elif item["level"] == 3:

            if level6_cnt != 0 or level5_cnt != 0 or level4_cnt != 0 or level3_cnt != 0:
                # 一つ前のデータの末端フラグをTrueにする
                res[-1]["leaf_flg"] = True

            level3_cnt += 1
            level3_currenttext = "/" + str(level1_cnt) + "-" + str(level2_cnt) + "-" + str(level3_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext + level2_currenttext + level3_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":False,"leveltext":leveltext,"level1":level1_cnt,"level2":level2_cnt,"level3":level3_cnt,"level4":0,"level5":0,"level6":0}
            level4_cnt = 0
            level5_cnt = 0
            level6_cnt = 0

        elif item["level"] == 4:

            if level6_cnt != 0 or level5_cnt != 0 or level4_cnt != 0:
                # 一つ前のデータの末端フラグをTrueにする
                res[-1]["leaf_flg"] = True

            level4_cnt += 1
            level4_currenttext = "/" + str(level1_cnt) + "-" + str(level2_cnt) + "-" + str(level3_cnt) + "-" + str(level4_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext + level2_currenttext + level3_currenttext + level4_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":False,"leveltext":leveltext,"level1":level1_cnt,"level2":level2_cnt,"level3":level3_cnt,"level4":level4_cnt,"level5":0,"level6":0}
            level5_cnt = 0
            level6_cnt = 0
            
        elif item["level"] == 5:
            
            if level6_cnt != 0 or level5_cnt != 0:
                # 一つ前のデータの末端フラグをTrueにする
                res[-1]["leaf_flg"] = True
            
            level5_cnt += 1
            level5_currenttext = "/" + str(level1_cnt) + "-" + str(level2_cnt) + "-" + str(level3_cnt) + "-" + str(level4_cnt) + "-" + str(level5_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext + level2_currenttext + level3_currenttext + level4_currenttext + level5_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":False,"leveltext":leveltext,"level1":level1_cnt,"level2":level2_cnt,"level3":level3_cnt,"level4":level4_cnt,"level5":level5_cnt,"level6":0}
            level6_cnt = 0
            
        elif item["level"] == 6:
            level6_cnt += 1
            level6_currenttext = "/" + str(level1_cnt) + "-" + str(level2_cnt) + "-" + str(level3_cnt) + "-" + str(level4_cnt) + "-" + str(level5_cnt) + "-" + str(level6_cnt) + "章 " + item["chapter_title"]
            leveltext:str = level1_currenttext + level2_currenttext + level3_currenttext + level4_currenttext + level5_currenttext + level6_currenttext
            temp = {"pageno_start":item["pageno_start"],"pageno_end":item["pageno_end"],"chapter_title":item["chapter_title"],"leaf_flg":True,"leveltext":leveltext,"level1":level1_cnt,"level2":level2_cnt,"level3":level3_cnt,"level4":level4_cnt,"level5":level5_cnt,"level6":level6_cnt}
       
        res.append(cast(type_chapter_per_page2,temp))
        pageno_start_last = item["pageno_start"]
            
    # 最後データの末端フラグをTrueにする
    res[-1]["leaf_flg"] = True
    
    if res[0]["pageno_start"] !=1: 
        # resの先頭にpageno_start=1のデータを追加する
        temp = {"pageno_start":1,"pageno_end":res[0]["pageno_start"]-1,"chapter_title":"タイトルページ","leaf_flg":True,"leveltext":"タイトルページ","level1":0,"level2":0,"level3":0,"level4":0,"level5":0,"level6":0}
        res.insert(0,cast(type_chapter_per_page2,temp))
    
    return res

import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import japanize_matplotlib
from tabulate import tabulate
import time
import random
from datetime import datetime, timedelta

@csrf_exempt
def code_interpreter(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        return HttpResponse("data:Error:デモモードではこの機能は利用できません。|E|".encode(), content_type='text/event-stream')
    else:
        print("Called "+ thisFunctionName)

    japanize_matplotlib.japanize() # matplotlibの日本語化
   
    session_id:str = ''
    chat_text:str = ''

    if request.method == 'GET':
        try:
            session_id = request.GET['session_id']
            chat_text = request.GET['chat_text']
        except Exception as e:
            print(f"An error occurred: {e}")
            res = {"status":"NG","data":f"入力パラメータが足りません。Error:{e}","image_url":"","data_url":"","exec_code":""}
            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2) 
            return HttpResponse(json_str)

    if request.method == 'POST':
        try:
            datas = json.loads(request.body)
    
            # requestには、param1,param2の変数がpostされたものとする
            para = datas["p"]
            pageid = datas["pageid"]
            session_id = datas["sessionid"]

            print(pageid)
            print(session_id)

            if para == "":
                errorMessage = "必要なパラメータがありません。"
                return errorMessage

            chat_text = para[-1]['content']  # 最後の値を取得 # type: ignore
            
            logger.info('[CodeInter:] '+ chat_text[0:1000] )
            
        except Exception as e:
            print(f"An error occurred: {e}")
            res = {"status":"NG","data":f"入力パラメータが足りません。Error:{e}","image_url":"","data_url":"","exec_code":""}
            logger.exception('['+thisFunctionName+']Error:' + str(e))

            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2) 
            return HttpResponse(json_str)

    csv_path:str = ''
    # csv_path = "C:\\Users\\tomohiku.FAREAST\\Downloads\\Persons.csv"

    df:pd.DataFrame
    if csv_path !='':
        # CSVファイルを読み込んでデータフレームに変換
        df = pd.read_csv(csv_path)
        df = optimize_df_types(df) # データフレームのデータ型を最適化する
    else:
        if session_id != '':
            container_name:str = azure_blob_container_for_codeinterpreter
            blob_name:str = 'input_' + str(session_id) + '.csv'
            df = get_from_blob_to_df(container_name=container_name,blob_name=blob_name)
            df = optimize_df_types(df) # データフレームのデータ型を最適化する
        else:
            res = {"status":"NG","data":f"session_id is none","image_url":"","data_url":"","exec_code":""}
            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2) 
            return HttpResponse(json_str)
            
    output:str = ''
    query:str = ''
    pycode:str = ''
    try:
        if chat_text == '':
            # 引数で質問を受ける
            question = "Last NameがA,B,Cから始まる人の数を多いもの順にそれぞれ教えてください。またグラフで見せてください。"
        else:
            question = chat_text
            
        query = create_query(question,df)

        # tempフォルダが無かったら作成する
        # フォルダのパス
        folder_path = "temp"
        # フォルダが存在しない場合は作成する
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{folder_path} フォルダを作成しました。")
        else:
            print(f"{folder_path} フォルダは既に存在します。")

        def code_interpreter_generator(pycode:str,output:str,session_id:str,folder_path:str):
            file_name:str = 'output_' + str(session_id)
            temperature_value:float = 0.7
            for i in range(3): # 3回までリトライする
                if i == 0:
                    prompt_temp:str = query.strip().replace('\n', '@n@').replace(' ', '@s@').replace('`', '‘')
                    yield f"data:コード生成のためのAI問い合わせ文（プロンプト）を生成✅@n@@n@@ps@{prompt_temp}@n@@n@@pe@@n@@n@コード生成をしています⏰@n@\n\n".encode()
                    # 処理時間の計測開始
                    start_time = time.time()
                    output = ""
                    print("first_prompt:\n",query)
                    pycode = get_openai_res(query,temperature_value,file_name,folder_path)
                    pycode_temp:str = pycode.strip().replace('\n', '@n@').replace(' ', '@s@')
                    
                    process_description:str = get_comment_from_code(pycode)
                    process_description = process_description.replace('\n', '@n@').replace(' ', '@s@')
                    
                    # 処理時間の計測終了
                    end_time = time.time()
                    interval:str = "生成時間: {:.1f}秒".format(end_time - start_time)
                    yield f"data:@s@➡️@s@コード生成が完了✅@s@@s@{interval}@n@@n@@ds@{process_description}@de@@n@@n@@cs@{pycode_temp}@ce@@n@@n@\n\n".encode()
                    print("code:\n",pycode)
                else:
                    retry_prompt:str = create_retry_prompt(pycode,output,query)
                    print("retry_prompt:\n",retry_prompt)
                    retry_prompt_temp:str = retry_prompt.strip().replace('\n', '@n@').replace(' ', '@s@').replace('`', '‘')
                    yield f"data:コード修正のためのAI問い合わせ文（プロンプト）を生成✅@n@@n@@ps@{retry_prompt_temp}@n@@n@@pe@@n@@n@コードの修正をしています⏰@n@\n\n".encode()

                    # 処理時間の計測開始
                    start_time = time.time()
                    pycode = get_openai_res(retry_prompt,temperature_value,file_name,folder_path)
                    pycode_temp:str = pycode.replace('\n', '@n@').replace(' ', '@s@')

                    process_description:str = get_comment_from_code(pycode)
                    process_description = process_description.replace('\n', '@n@').replace(' ', '@s@')

                    # 処理時間の計測終了
                    end_time = time.time()
                    interval:str = "修正時間: {:.1f}秒".format(end_time - start_time)
                    yield f"data:@s@➡️@s@コード修正が完了✅@n@@n@@ds@{process_description}@de@@n@@n@@cs@{pycode_temp}@ce@@n@@n@\n\n".encode()
                    print("code:\n",pycode)

                # pythonコードを実行
                yield f"data:コードを実行しています⏰@n@\n\n".encode()

                # 処理時間の計測開始
                start_time = time.time()

                output = exec_python_code(pycode,df)

                # 処理時間の計測終了
                end_time = time.time()
                interval:str = "実行時間: {:.1f}秒".format(end_time - start_time)

                # outputに"Error"文言が含まれていない場合はループを抜ける
                if "Error message:" not in output:
                    print("コード実行が完了")
                    yield f"data:@s@➡️@s@コード実行が完了✅@s@@s@{interval}@n@@n@【結果の表示】@n@@n@\n\n".encode()
                    break
                else:
                    print("生成されたコードがエラーのため、生成をリトライして再実行します")
                    yield f"data:@s@➡️@s@コード実行が失敗🚨修正してリトライします。ごめんなさい🙏@n@@n@\n\n".encode()
                            
            if type(output) == str:
                output = output.strip()
            else:
                output = str(output).strip()
            
            print("output:\n",output.strip())

            sas_url:str = ''
            file_path:str = folder_path + '\\' + file_name + '.png'
            # file_name:str = 'output_' + str(session_id) + '.png'
            container_name:str = azure_blob_container_for_codeinterpreter
            if os.path.exists(file_path):
                print('output.png exists')
                res2:str = handle_uploaded_file2(file_path,file_name + '.png',container_name)
                if res2 == "OK":
                    print("output.png upload OK")
                    os.remove(file_path)
                    sas_url = get_sasurl(file_name + '.png',container_name)
                else:
                    print(res2)
            else:
                print('output.png does not exist')
                
            sas_url_data:str = ''
            file_path_data:str = folder_path + '\\' + file_name + '.xlsx'
            # file_name_data:str = 'output_' + str(session_id) + '.xlsx'  
            container_name_data:str = azure_blob_container_for_codeinterpreter
            if os.path.exists(file_path_data):
                print('output.xlsx exists')
                res3:str = handle_uploaded_file2(file_path_data,file_name + '.xlsx',container_name_data)
                if res3 == "OK":
                    print("output.xlsx upload OK")
                    os.remove(file_path_data)
                    sas_url_data = get_sasurl(file_name + '.xlsx',container_name_data)
                else:
                    print(res3)
            else:
                print('output.xlsx does not exist')

            
            # process_description:str = get_comment_from_code(pycode)
            res = {"status":"OK","data":output,"image_url":sas_url,"data_url":sas_url_data}
            # res = output +"-"+ process_description+"-"+ sas_url+"-data_url-"+sas_url_data + "-exec_code-" +pycode

            output = ''
            sas_url = ''
            sas_url_data = ''
            pycode = ''

            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2)
            yield ("data:@n@@js@" + json_str.replace('\n', '@n@').replace(' ', '@s@') + "@je@\n\n").encode()
            yield "data:|E|\n".encode()
            # return HttpResponse(json_str)
        return StreamingHttpResponse(code_interpreter_generator(pycode=pycode,output=output,session_id=session_id,folder_path=folder_path), content_type='text/event-stream')

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.exception('['+thisFunctionName+']Error:' + str(e) )

        res = {"status":"NG","data":f"An error occurred: {e}","image_url":"","data_url":"","exec_code":""}
        #json形式の文字列を生成
        json_str = json.dumps(res, ensure_ascii=False, indent=2) 
        return HttpResponse(json_str)


@csrf_exempt
def code_interpreter_sql(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        return HttpResponse("data:Error:デモモードではこの機能は利用できません。|E|".encode(), content_type='text/event-stream')
    else:
        print("Called "+ thisFunctionName)

    session_id:str = ''
    chat_text:str = ''
    schemaname:str = ""
    tablename:str = ""

    if request.method == 'POST':
        try:
            datas = json.loads(request.body)
    
            # requestには、param1,param2の変数がpostされたものとする
            para = datas["p"]
            pageid = datas["pageid"]
            session_id = datas["sessionid"]
            schemaname = datas["schemaname"]
            tablename = datas["tablename"]        

            print(pageid)
            print(session_id)

            if para == "":
                # exceptionを発生させる
                raise Exception("必要なパラメータがありません。")

            chat_text = para[-1]['content']  # 最後の値を取得 # type: ignore
            
            logger.info('[CodeInter:] '+ chat_text[0:1000] )
            
        except Exception as e:
            print(f"An error occurred: {e}")
            res = {"status":"NG","data":f"入力パラメータが足りません。Error:{e}","image_url":"","data_url":"","exec_code":""}
            logger.exception('['+thisFunctionName+']Error:' + str(e))

            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2) 
            return HttpResponse(json_str)
           
    try:
        output:str = ''
        prompt:str = ''
        sqlcode:str = ''
        df:pd.DataFrame = pd.DataFrame()
        if chat_text == '':
            # Exceptionを発生させる
            raise Exception("質問が入力されていません。")
        
        # テーブルレイアウトを取得
        df = get_sql_tablerayout(schemaname,tablename)
        # df = pd.DataFrame(tablerayout, columns=["ORDINAL_POSITION", "COLUMN_NAME", "DATA_TYPE", "CHARACTER_MAXIMUM_LENGTH"])

        # プロンプトを作成
        prompt = create_sql_prompt(chat_text,schemaname,tablename,df.to_markdown())
        
        # tempフォルダが無かったら作成する
        # フォルダのパス
        folder_path = "temp"
        # フォルダが存在しない場合は作成する
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{folder_path} フォルダを作成しました。")
        else:
            print(f"{folder_path} フォルダは既に存在します。")

        def code_interpreter_generator(prompt:str,sqlcode:str,output:str,session_id:str,folder_path:str):
            df2:pd.DataFrame = pd.DataFrame()

            file_name:str = 'output_' + str(session_id)
            temperature_value:float = 0.7
            for i in range(3): # 3回までリトライする
                if i == 0:
                    prompt_temp:str = prompt.strip().replace('\n', '@n@').replace(' ', '@s@').replace('`', '‘')
                    yield f"data:コード生成のためのAI問い合わせ文（プロンプト）を生成✅@n@@n@@ps@{prompt_temp}@n@@n@@pe@@n@@n@コード生成をしています⏰@n@\n\n".encode()
                    # 処理時間の計測開始
                    start_time = time.time()
                    output = ""
                    print("first_prompt:\n",prompt)
                    # OpenAIでプロンプトを実行し、SQLコードを生成
                    sqlcode = call_openai_create_sql(prompt,temperature_value)
                    # pycode = get_openai_res(prompt,temperature_value,file_name,folder_path)
                    sqlcode_temp:str = sqlcode.strip().replace('\n', '@n@').replace(' ', '@s@')
                    
                    process_description:str = get_comment_from_sql_code(sqlcode)
                    process_description = process_description.replace('\n', '@n@').replace(' ', '@s@')
                    
                    # 処理時間の計測終了
                    end_time = time.time()
                    interval:str = "生成時間: {:.1f}秒".format(end_time - start_time)
                    yield f"data:@s@➡️@s@コード生成が完了✅@s@@s@{interval}@n@@n@@ds@{process_description}@de@@n@@n@@cs@{sqlcode_temp}@ce@@n@@n@\n\n".encode()
                    print("code:\n",sqlcode)
                else:
                    retry_prompt:str = create_retry_sql_prompt(sqlcode,output,prompt)
                    print("retry_prompt:\n",retry_prompt)
                    retry_prompt_temp:str = retry_prompt.strip().replace('\n', '@n@').replace(' ', '@s@').replace('`', '‘')
                    yield f"data:コード修正のためのAI問い合わせ文（プロンプト）を生成✅@n@@n@@ps@{retry_prompt_temp}@n@@n@@pe@@n@@n@コードの修正をしています⏰@n@\n\n".encode()

                    # 処理時間の計測開始
                    start_time = time.time()
                    sqlcode = call_openai_create_sql(retry_prompt,temperature_value)
                    sqlcode_temp:str = sqlcode.replace('\n', '@n@').replace(' ', '@s@')

                    process_description:str = get_comment_from_sql_code(sqlcode)
                    process_description = process_description.replace('\n', '@n@').replace(' ', '@s@')

                    # 処理時間の計測終了
                    end_time = time.time()
                    interval:str = "修正時間: {:.1f}秒".format(end_time - start_time)
                    yield f"data:@s@➡️@s@コード修正が完了✅@n@@n@@ds@{process_description}@de@@n@@n@@cs@{sqlcode_temp}@ce@@n@@n@\n\n".encode()
                    print("code:\n",sqlcode)

                # pythonコードを実行
                yield f"data:コードを実行しています⏰@n@\n\n".encode()

                # 処理時間の計測開始
                start_time = time.time()

                # SQLコードを実行し、結果を取得
                result:tuple[str,pd.DataFrame] = exec_sql(sqlcode)
                output,df2 = result
              
                print(df2.to_markdown())

                # 処理時間の計測終了
                end_time = time.time()
                interval:str = "実行時間: {:.1f}秒".format(end_time - start_time)

                # outputに"Error"文言が含まれていない場合はループを抜ける
                if "Error message:" not in output:
                    print("コード実行が完了")
                    yield f"data:@s@➡️@s@コード実行が完了✅@s@@s@{interval}@n@@n@【結果の表示】@n@@n@\n\n".encode()
                    break
                else:
                    print("生成されたコードがエラーのため、生成をリトライして再実行します")
                    yield f"data:@s@➡️@s@コード実行が失敗🚨修正してリトライします。ごめんなさい🙏@n@@n@\n\n".encode()

            output = "取得情報をExcelファイルに出力しました。\n\n【出力した表の先頭5行】\n\n" + df2.head().to_markdown()
            
            print("output:\n",output.strip())
            
            # imageはなし
            sas_url = ''
              
            sas_url_data:str = ''
            file_path_data:str = folder_path + '\\' + file_name + '.xlsx'

            # SQLの処理結果df2のデータをEXCELに出力
            df2.to_excel(file_path_data, index=False)

            container_name_data:str = azure_blob_container_for_codeinterpreter
            if os.path.exists(file_path_data):
                print('output.xlsx exists')
                res3:str = handle_uploaded_file2(file_path_data,file_name + '.xlsx',container_name_data)
                if res3 == "OK":
                    print("output.xlsx upload OK")
                    os.remove(file_path_data)
                    sas_url_data = get_sasurl(file_name + '.xlsx',container_name_data)
                else:
                    print(res3)
            else:
                print('output.xlsx does not exist')

            
            # process_description:str = get_comment_from_code(pycode)
            res = {"status":"OK","data":output,"image_url":sas_url,"data_url":sas_url_data}
            # res = output +"-"+ process_description+"-"+ sas_url+"-data_url-"+sas_url_data + "-exec_code-" +pycode

            output = ''
            sas_url = ''
            sas_url_data = ''
            sqlcode = ''

            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2)
            yield ("data:@n@@js@" + json_str.replace('\n', '@n@').replace(' ', '@s@') + "@je@\n\n").encode()
            yield "data:|E|\n".encode()
            # return HttpResponse(json_str)
        return StreamingHttpResponse(code_interpreter_generator(prompt=prompt,sqlcode=sqlcode,output=output,session_id=session_id,folder_path=folder_path), content_type='text/event-stream')

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.exception('['+thisFunctionName+']Error:' + str(e) )

        res = {"status":"NG","data":f"An error occurred: {e}","image_url":"","data_url":"","exec_code":""}
        #json形式の文字列を生成
        json_str = json.dumps(res, ensure_ascii=False, indent=2) 
        return HttpResponse(json_str)

### sql code_interpreter系の関数

def get_sql_tablerayout(schemaname:str,tablename:str) -> pd.DataFrame:
    thisFunctionName: str = sys._getframe().f_code.co_name

    # SQLクエリを実行
    sqlcode = f'''  
        SELECT ORDINAL_POSITION,COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH
        from INFORMATION_SCHEMA.COLUMNS
        WHERE Table_schema = '{schemaname}' AND TABLE_NAME = '{tablename}'
    '''
    
    # 結果を取得
    result = ''
    df:pd.DataFrame = pd.DataFrame()
    try:   
        # SQLクエリを実行
        with connection.cursor() as cursor:
            cursor.execute(sqlcode)
            result = cursor.fetchall()
            
        if result == '':
            # exceptionを発生させる
            raise Exception("指定されたテーブルが存在しません。")
        
        df = pd.DataFrame(result)
        if cursor.description != None:
            # 列名を自動的に取得
            columns = [desc[0] for desc in cursor.description]
            df.columns = columns
            
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.exception('['+thisFunctionName+']Error:' + str(e) )
        
    return df

def get_sql_tablehead(schemaname:str,tablename:str) -> pd.DataFrame:
    thisFunctionName: str = sys._getframe().f_code.co_name

    # SQLクエリを実行
    sqlcode = f'''  
        SELECT *
        FROM {schemaname}.{tablename}
        LIMIT 5
    '''
    
    # 結果を取得
    df:pd.DataFrame = pd.DataFrame()
    output,df = exec_sql(sqlcode)

    if "Error message:" in output:
        # exceptionを発生させる
        raise Exception("SQLの実行結果がErrorです。"+output)        
    return df

def get_sql_table_summary(schemaname:str,tablename:str) -> pd.DataFrame:
    thisFunctionName: str = sys._getframe().f_code.co_name

    # SQLクエリを実行
    sqlcode = f'''
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{tablename}' AND table_schema = '{schemaname}'
        ORDER BY ordinal_position
    '''
        #  AND (data_type LIKE '%date%' OR data_type LIKE '%int%' OR data_type LIKE '%numeric%' OR data_type LIKE '%time%' OR data_type LIKE '%float%');
    
    # 結果を取得
    df:pd.DataFrame = pd.DataFrame()
    output,df = exec_sql(sqlcode)

    if "Error message:" in output:
        # exceptionを発生させる
        raise Exception("SQLの実行結果がErrorです。"+output)  

    sqlcode = ''
    # dfの件数分だけループ
    for index, row in df.iterrows():
        if sqlcode != '':
            sqlcode += " UNION ALL "
        # df内のdata_type列の値によって処理を分岐
        if row.data_type == "date":
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'日付' AS データ型, TO_CHAR(MIN({row.column_name}), 'YYYY/MM/DD') AS 最小値, TO_CHAR(MAX({row.column_name}), 'YYYY/MM/DD') AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", '-' AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        elif row.data_type == "timestamp" or row.data_type == "timestamp without time zone" or row.data_type == "timestamp with time zone":
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'日時' AS データ型, TO_CHAR(MIN({row.column_name}), 'YYYY/MM/DD HH24:MI:SS') AS 最小値, TO_CHAR(MAX({row.column_name}), 'YYYY/MM/DD HH24:MI:SS') AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", '-' AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        elif row.data_type == "time":
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'時間' AS データ型, TO_CHAR(MIN({row.column_name}), 'HH24:MI:SS') AS 最小値, TO_CHAR(MAX({row.column_name}), 'HH24:MI:SS') AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", '-' AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        elif row.data_type == "integer" or row.data_type == "bigint" or row.data_type == "smallint" or row.data_type == "money" or row.data_type == "smallmoney" or row.data_type == "decimal" or row.data_type == "real" :
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'数値' AS データ型, TO_CHAR(MIN({row.column_name}), 'FM999,999,999') AS 最小値, TO_CHAR(MAX({row.column_name}), 'FM999,999,999') AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", '-' AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        elif row.data_type == "numeric" or row.data_type == "double precision" or row.data_type == "decimal" or row.data_type == "float":
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'小数有り数値' AS データ型, TO_CHAR(MIN({row.column_name}), 'FM999,999,999.9') AS 最小値, TO_CHAR(MAX({row.column_name}), 'FM999,999,999.9') AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", '-' AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        elif row.data_type == "character" or row.data_type == "character varying" or row.data_type == "text":
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'文字列' AS データ型, '-' AS 最小値, '-' AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", TO_CHAR(COUNT(DISTINCT {row.column_name}), 'FM999,999,999') AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''
        else:
            sqlcode += f'''
                SELECT '{row.column_name}' AS 列名,'その他' AS データ型, '-' AS 最小値, '-' AS 最大値
                ,COUNT(CASE WHEN {row.column_name} is NULL THEN 1 END) AS "空白行の数", TO_CHAR(COUNT(DISTINCT {row.column_name}), 'FM999,999,999') AS 値の種類数, COUNT(*) AS 行数
                FROM {schemaname}.{tablename}
            '''

    # 結果を取得
    df2:pd.DataFrame = pd.DataFrame()
    output,df2 = exec_sql(sqlcode)

    return df2

def create_sql_prompt(query:str,schemaname:str,tablename:str,dbrayout_text:str) -> str:
    prompt:str = f'''
    SQLのコードを以下の条件に合わせて作成してください。

    # 要件
    {query}
    ## コードで順守すべき規約
    - フォーマットの変更はWITH関数の中では行わず、最後のSELECT文のみで行ってください。
    - syntax errorにならないようコードを作成してください。
    - timestampやdate,time型の列のタイムゾーンは変更しないでください。 AT TIME ZONE は使わないでください。
    - コード内の先頭にはコメントを入れてください。コメントは日本語で、処理の流れを詳細に説明してください。また専門用語は使わず、SQLのコードが読めない人も理解できるようにしてください。

    # DBMS
    PostgreSQL

    # table name
    {schemaname}.{tablename}

    # data rayout
    {dbrayout_text}
    '''
    # 各行の前の空白と語尾の空白を削除
    prompt = "\n".join([line.strip() for line in prompt.split("\n")])

    print("prompt:\n",prompt)
    return prompt.strip()

def create_retry_sql_prompt(sqlcode:str,err:str,prequery:str) -> str:

    retry_prompt:str = "SQLコードを実行するとエラーになりました。\n実行したSQLコードとErrorメッセージを確認し、SQLコードがエラーにならないように修正してください。\
    \n\n- 実行したSQLコード\
    \n```sql\n\n" + sqlcode + "```\n- Errorメッセージ\n```\n" + err + "\n```"\
    + "\n\n上記のSQLコードはGPT-4により生成しました。その時に使ったプロンプトを以下に記載します。コード修正の参考にしてください。\n- コード生成に使用したプロンプト\
    \n```\n" + prequery + "\n```"

    # print("retry_query:\n",query)

    return retry_prompt

def call_openai_create_sql(prompt:str,temperature_value:float) -> str:
    
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key

    response = openai.ChatCompletion.create(
                engine="gpt-4",
                # model="gpt-4-0613",
                messages=[
                {"role": "system", "content":"You are a technical assistant specialized in IT and programming.Respond using markdown."},
                {"role": "user","content": prompt}
                ],
                temperature=temperature_value,
                max_tokens=1000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
            )
    message = response.choices[0]["message"]["content"].strip() # type: ignore
    print("retry_message_origin:\n",message)
    
    sqlcode_origin = extract_sql_code(message)
    sqlcode_origin = str(sqlcode_origin)
    return sqlcode_origin

def extract_sql_code(string) -> str:
    string = string.replace('```SQL','```sql')
    
    pattern = r'```sql\n(.*?)```\n'
    matches = re.findall(pattern, string, re.DOTALL)

    if matches:
        code = '\n'.join(matches)
        return code
    else:
        return ""

from django.db import connection

def exec_sql(sqlcode:str) -> tuple[str,pd.DataFrame]:
    
    df:pd.DataFrame = pd.DataFrame()
    try:
        if sqlcode == None:
            res = "Error message: sqlコードがありません。"
        else:        
   
            # SQLクエリを実行
            with connection.cursor() as cursor:
                cursor.execute(sqlcode)
                result = cursor.fetchall()

            df = pd.DataFrame(result)
            if cursor.description != None:
                # 列名を自動的に取得
                columns = [desc[0] for desc in cursor.description]
                df.columns = columns

            res = "OK"

    except Exception as e:
        res:str = f"Error message: {e}"
        print(f"exec_sql_code error:{res}")
    return res,df

    
def get_comment_from_sql_code(code_str:str) -> str:

    # SQLのコメントを取り出す正規表現
    # comment_regex = r'--.*$|/\*.*?\*/'
    comment_regex = r'/\*.*?\*/|--.*?$'

    # コメント行のリストを作成する
    comment_lines = []
    for line in code_str.split('\n'):
        if re.match(comment_regex, line):
            comment_lines.append(line.strip())

    comment_str:str = '\n'.join(comment_lines).strip()
    comment_str = comment_str.replace('--','1.')
    return comment_str

### python code_interpreter系の関数

def get_comment_from_code(code_str:str) -> str:

    # コメントを取り出す正規表現（行頭以外のコメントも含む）
    comment_regex = r'(^\s*#.*$|(?<=\s)#.*$)'

    # コメント行のリストを作成する
    comment_lines = []
    for line in code_str.split('\n'):
        if re.match(comment_regex, line):
            comment_lines.append(line.strip())

    comment_str:str = '\n'.join(comment_lines).strip()
    comment_str = comment_str.replace('#','1.')
    return comment_str

def optimize_df_types(df:pd.DataFrame) -> pd.DataFrame:

    # str型の項目に対して日付型に変換できるかどうかをチェックし、変換する
    for col in df.select_dtypes(include=['object']).columns:
        try:
            if ':' in df[col].iloc[0]:
                if len(df[col].iloc[0]) == 5:  # 5桁の場合は秒を補完する
                    df[col] = df[col].apply(lambda x: str(x).replace("24:","00:").replace("25:","01:").replace("26:","02:").replace("27:","03:").replace("28:","04:").replace("29:","05:") + ':00' if len(str(x)) == 5 else x)
                    df[col] = pd.to_datetime(df[col]).dt.time
                    print(f'{col}: Converted to time')
                elif len(df[col].iloc[0]) == 8:
                    df[col] = df[col].apply(lambda x: str(x).replace("24:","00:").replace("25:","01:").replace("26:","02:").replace("27:","03:").replace("28:","04:").replace("29:","05:") if len(str(x)) == 8 else x)
                    df[col] = pd.to_datetime(df[col]).dt.time
                    print(f'{col}: Converted to time')
                elif '/' in df[col].iloc[0] or '-' in df[col].iloc[0]:
                    df[col] = pd.to_datetime(df[col])
                    print(f'{col}: Converted to datetime')
                else:
                    print(f'{col}: Should not converted to datetime')
            else:
                this_year:str = datetime.now().strftime("%Y")
                if '/' in df[col].iloc[0]:
                    df[col] = df[col].apply(lambda x: this_year + '/' + str(x) if len(str(x)) == 5 else x) # 5桁の場合は年を補完する
                    df[col] = pd.to_datetime(df[col])
                    print(f'{col}: Converted to date')
                elif '-' in df[col].iloc[0]:
                    df[col] = df[col].apply(lambda x: this_year + '-' + str(x) if len(str(x)) == 5 else x) # 5桁の場合は年を補完する
                    df[col] = pd.to_datetime(df[col])
                    print(f'{col}: Converted to date')
                else:
                    print(f'{col}: Should not converted to datetime')
        except ValueError as e:
            print(f'{col}: Cannot be converted. Error:{e}')
        except Exception as e:
            print(f'{col}: Cannot be converted. Error:{e}')

    return df

def extract_python_code(string) -> str:
    string = string.replace('```PYTHON','```python')
    string = string.replace('```Python','```python')
    
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, string, re.DOTALL)

    if matches:
        code = '\n'.join(matches)
        return code
    else:
        return ""

def remove_import_block(string,keword) -> str:
    lines = string.split('\n')
    modified_lines = []

    skip_block = False
    for line in lines:
        if line.startswith(keword):
            skip_block = True
        elif line == '' and skip_block:
            skip_block = False
        if not skip_block:
            modified_lines.append(line)

    modified_string = '\n'.join(modified_lines)
    return modified_string

def replace_code_block(string:str,filename:str,folder_path:str) -> str:
    res:str = string.replace('plt.show()','plt.savefig(\'' + folder_path + '\\' + filename + '.png\', bbox_inches=\'tight\')')
    res:str = res.replace('output = python_function(df)','')
    res:str = res.replace('\noutput = python_function(df)','')
    res:str = res.replace('\npython_function(df)','')
    res:str = res.replace('\noutput\n','')
    res:str = res.replace('\nprint(output)','')
    # res:str = res.replace('CSV','Excel')
    # res:str = res.replace('csv','Excel')

    # 正規表現パターン plt.saveflgのファイル名が指定の名前と違う場合の置換え
    pattern1 = r"plt\.savefig\('(.+?)'\)"
    res = re.sub(pattern1, r"plt.savefig('" + folder_path + r"\\" + filename + r".png', bbox_inches='tight')", res)

    # 正規表現パターン Excelファイル名が指定の名前と違う場合の置換え
    pattern2 = r"'[^']*\.xlsx'" # 'で囲まれた文字列の中に.xlsxが含まれている場合
    res = re.sub(pattern2, r"'" + folder_path + r"\\" + filename + r".xlsx'", res)
    
    # 正規表現パターン　Function名が指定の名前と違う場合の置換え
    pattern3 = r"def\s+(\w+)\("
    res = re.sub(pattern3, r"def python_function(", res)

    # 正規表現パターン
    pattern4 = r"\noutput =.*\n"
    res = re.sub(pattern4, r"\n", res)

    # 正規表現パターン
    pattern5 = r"\noutput =.*`"
    res = re.sub(pattern5, r"\n", res)
    
    return res

def get_openai_res(prompt:str,temperature_value:float,filename:str,folder_path:str) -> str:

    ### Azure ###
    # APIキーの設定
    openai.api_type = "azure"
    openai.api_base = azure_api_base
    openai.api_version = azure_api_version
    openai.api_key = azure_api_key

    response = openai.ChatCompletion.create(
                engine="gpt-4-32k",
                messages=[
                {"role": "system", "content":"You are a technical assistant specialized in IT and programming.Respond using markdown."},
                {"role": "user","content": prompt}
                ],
                temperature=temperature_value,
                max_tokens=3000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
            )
    
    ### Open AI ###
    # # APIキーの設定
    # openai.api_type = "openai"
    # openai.api_base = openai_api_base
    # openai.api_version = openai_api_version
    # openai.api_key = openai_api_key

    # response = openai.ChatCompletion.create(
    #             model="gpt-4-0613",
    #             messages=[
    #             {"role": "system", "content":"You are a technical assistant specialized in IT and programming.Respond using markdown."},
    #             {"role": "user","content": question}
    #             ],
    #             temperature=temperature_value,
    #             max_tokens=1000,
    #             top_p=0.95,
    #             frequency_penalty=0,
    #             presence_penalty=0,
    #             stop=None,
    #             stream=False,
    #         )
    
    message = response.choices[0]["message"]["content"].strip() # type: ignore
    print("message_origin:\n",message)

    pycode_origin = extract_python_code(message)
    pycode_origin = str(pycode_origin)
    print("python_origin:\n",pycode_origin)
    pycode = remove_import_block(pycode_origin,'import')
    pycode = remove_import_block(pycode,'from')
    pycode = remove_import_block(pycode,'df =')
    pycode = remove_import_block(pycode,'output =')
    pycode = remove_import_block(pycode,'# ')
    pycode = replace_code_block(pycode,filename,folder_path)
    print("pycode:\n",pycode)

    return pycode

def create_retry_prompt(pycode:str,err:str,prequery:str) -> str:

    retry_prompt:str = "Pythonコードを実行するとエラーになりました。\n実行したPythonコードとErrorメッセージを確認し、Pythonコードがエラーにならないように修正してください。\
    \n\n- 実行したPythonコード\
    \n```python\n" + pycode + "```\n\n- Errorメッセージ\n```\n" + err + "\n```"\
    + "\n\n上記のPythonコードはGPT-4により生成しました。その時に使ったプロンプトを以下に記載します。コード修正の参考にしてください。\n- コード生成に使用したプロンプト\
    \n```\n" + prequery + "\n```"

    # print("retry_query:\n",query)

    return retry_prompt
    
def create_query(text:str,df:pd.DataFrame) -> str:
    
    # csv出力は未対応なのでExcelに書き換える
    text = text.replace('csv', 'Excel').replace('CSV', 'Excel').replace('Csv', 'Excel')
    
    data_layout_temp:object = df.dtypes
    data_layout:str = data_layout_temp.to_markdown()
    data_head_temp:object = df.head()
    data_head:str = data_head_temp.to_markdown()
    sample_ammount:int = 100
    if df.shape[0] < 100:
        sample_ammount = df.shape[0]
    sample:pd.DataFrame = df.sample(n=sample_ammount)
    data_types_temp = sample.applymap(type)
    data_types = data_types_temp.drop_duplicates().to_markdown()
    data_describe_temp:object = df.describe()
    data_describe:str = data_describe_temp.to_markdown()
    
    query = "次の条件を満たしたpythonのコードを作成してください。\n\n- コードの要件\n  - " + text + \
    "\n\n- コードで順守すべき規約\
        \n  - コードの出力フォーマットに関しての規約\
        \n    - def python_function(df: pd.DataFrame) -> str:で定義されるFunction内のコードを出力してください。入力パラメータのdfはデータセット済みのpandasのデータフレームです。\
        \n    - 出力するコードは必ずpython_function関数内だけにしてください。複数の関数を作らないでください。\
        \n    - importは関数中に出力してください。\
        \n    - コードは分割して出力せず、１つのインラインとして出力してください。\
        \n    - コード内に記述するコメントやラベル名も全て日本語で出力してください。\
        \n    - コード内でバッククォートは使わないでください。バッククォートにより、Markdownが崩れる場合はあるためです。例:「```」\
        \n    - このコードはインタラクティブなターミナルでは実行されないため、printなどの関数を使わず、変数名を指定しての出力は行わないでください。例:df.head()など\
        \n  - コード内コメントに関しての規約\
        \n    - コード内コメントは可能な限り詳しく説明してください。\
        \n    - コード内コメントはプログラマーではない人でも利用できるよう専門的な用語はできるだけ少なくしてください。'データフレーム'は'入力データ'と呼んでください。\
        \n    - コード内コメントは体言止めは使わず、リズムの良い文章にしてください。\
        \n  - エラーハンドリングに関しての規約\
        \n    - コードをエラーが発生していもエラーハンドリングはしないでください。try文は使用禁止です。\
        \n    - コードでエラーが発生した場合はraise Exceptionで例外をスローしてください。\
        \n    - 次のエラーが発生しやすいことが実績からわかっています。発生しないように考慮をしてください。\
        \n      - Error1: Cannot mask with non-boolean array containing NA / NaN values\
        \n      - Error2: Can only use .dt accessor with datetimelike values\
        \n      - Error3: Could not convert\
        \n      - Error4: 'DataFrame' object has no attribute 'append'\
        \n    - pythonの 'DataFrame' object から 'append' attributeは削除されていますので、使わないでください。\
        \n    - Pythonのコードは型定義を省略せず、型を意識してコードを考えてください。特に値の移動時に型変換が必要な場合はエラーが発生しないように回避するコードを加えてください。\
        \n    - コード内でtriple-quoted string literalは使わないでください。\
        \n    - コード内でpandasのdt アクセサを使用する場合は、列が datetime 型であることを確認してから使用してください。確認するコード例:if pd.api.types.is_datetime64_any_dtype(df['date']):\
        \n  - importするライブラリに関する規約\
        \n    - pandasはバージョン1.3.2で利用できる関数のみをコードにしてください。\
        \n    - matplotlibはバージョン3.4.2で利用できる関数のみをコードにしてください。\
        \n    - tabulateはバージョン0.8.9で利用できる関数のみをコードにしてください。\
        \n    - XlsxWriterはバージョン1.4.3で利用できる関数のみをコードにしてください。\
        \n  - ファイルの出力に関する規約\
        \n    - ファイルの出力先はtempディレクトリ配下にしてください。tempディレクトリは既に存在する前提で考慮ください。\
        \n    - Excelファイルを作成する場合は'with pd.ExcelWriter('temp\\output.xlsx', engine='xlsxwriter') as writer:'を使ってください。\
        \n  - matplotlibを使ったグラフに関する規約\
        \n    - matplotlibを使ってグラフを作成する場合は'plt.show()'関数を使ってください。\
        \n    - コード内でpadasのplot()を使った場合は必ずplt.show()もコード内に出力してください。\
        \n    - matplotlibのグラフは凡例やラベルの数が多すぎると文字が重なり、読めなくなります。そのため、グラフや表は最大20件までのラベルになるようにデータ量を減らして作成してください。20件を超える場合は、削減する条件を明示してください。例:データ量が多いため上位20件にデータを絞ってグラフ化しています。\
        \n    - グラフや表は最大20件までの列データになるようにデータ量を減らして作成してください。\
        \n    - グラフや表を作成するために利用したデータはto_excel()を使って'temp\\output.xlsx'に出力してください。実行例:df_after_processing.to_excel('temp\\output.xlsx', index=False)。Excelファイルを作成する理由は、グラフや表が正しいことを確認するために元となったデータをExcelで参照するためです。\
        \n  - return値のoutputに関する規約\
        \n    - returnは関数で最後に1つのみにしてください。\
        \n    - return値のoutputに記載する内容は次のとおり。処理の成功時は処理内容の説明を詳細に記載してください。処理のエラー時はエラー内容を詳細に説明してください。また出力ファイル名は記載してはいけません。\
        \n    - 表を出力の場合はprint関数は利用せず、markdown形式で回答を作成し、outputという名前の変数に格納してください。回答はoutputという名前の変数1つにまとめて格納してください。\
        \n    - データフレームをoutputに格納する場合は.to_string()ではなく、.to_markdown()を使ってください。例:output = df.to_markdown()。Markdownで作成する理由はWeb画面上でHTMLに変換して質問者に提示する際、表や段落などがMarkdown形式の方が見やすいからです。\
        \n\n- Input parameter 'df: pd.DataFrame' data layout \n\n"\
        + data_layout\
        + "\n\n- Input parameter 'df: pd.DataFrame' data types\n\n"\
        + data_types\
        + "\n\n- Input parameter 'df: pd.DataFrame' data desctibe\n\n"\
        + data_describe\
        + "\n\n- Input parameter 'df: pd.DataFrame' data head\n\n"\
        + data_head\

    # print("query:\n",query)
    return query

def exec_python_code(pycode:str,df:pd.DataFrame) -> str:
    res:str = ""
    try:
        if pycode == None:
            res = "コードが生成できませんでした。"
        else:        
            exec(pycode,globals())
        
        # 関数の存在確認
        if callable(python_function):  # type: ignore
            print("python_function is defined.")
            res = python_function(df=df) # type: ignore
            return res
        else:
            print("python_function is not defined.")
            return "コードが生成できませんでした。"

    except Exception as e:
        res:str = f"Error message: {e}"
        print(f"exec_python_code error:{res}")
        return res

###
from django.conf import settings
@csrf_exempt
def code_interpreter_upload_csv(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    print("Called "+ thisFunctionName)
    
    container_name:str = azure_blob_container_for_codeinterpreter
    
    res = {}
    if request.method == 'POST':
        try:
            form = ''
            presetfile:str = ''
            if 'presetfile' in request.POST:
                presetfile = request.POST['presetfile']
                form = UploadFileFormForCodeInterpriterWithoutFile(request.POST)
            else:
                form = UploadFileFormForCodeInterpriter(request.POST, request.FILES)
            if form.is_valid():
                sys.stderr.write("*** file_upload *** \n")
                session_id = request.POST['session_id']
                file_obj = ''
                
                file_name:str = 'input_' + session_id + '.csv'  
                res2:str = ''
                df:pd.DataFrame
                if presetfile != '':
                    container_name:str = azure_blob_container_for_csvpreset
                    blob_name:str = presetfile
                    df = get_from_blob_to_df(container_name=container_name,blob_name=blob_name)                    
                    res2 = copy_from_blob_to_blob(src_blob_name=blob_name,src_container_name=container_name,dst_blob_name=file_name,dst_container_name=azure_blob_container_for_codeinterpreter)
                else:
                    file_obj = request.FILES['file']
                    df = pd.read_csv(file_obj) # type: ignore
                    res2 = handle_uploaded_file(file_obj,file_name,container_name)
                                
                if res2 == "OK":
                    df = optimize_df_types(df) # データフレームのデータ型を最適化する
                    data_head:str = df.head().to_markdown()
                    data_head = data_head.replace(' 00:00:00', '')
                    data_describe:str = df.describe().to_markdown()
                    data_describe = data_describe.replace('count', '行数').replace('mean', '平均').replace('std', '標準偏差').replace('min', '最小値').replace('max', '最大値')
                    data_dateime_columns:str = get_datetime_columns(df)
                    res = { "status": "OK", "datarayout": data_head,"data_describe":data_describe,"dateime_columns":data_dateime_columns }
                else:
                    res = { "status": "NG " + str(res2)}
                                    
            else:
                sys.stderr.write("*** file_upload *** \n")
                sys.stderr.write("Error:" + str(form.errors)+"\n")
                res = { "status": "NG " + str(form.errors)}

        except Exception as e:
            print(f"An error occurred: {e}")
            logger.exception('['+thisFunctionName+']Error:' + str(e) )

            res = {"status":"NG CSVが読み込めません。フォーマットを確認ください。Error:{e}"}
    
    #json形式の文字列を生成
    json_str = json.dumps(res, ensure_ascii=False, indent=2) 
    return HttpResponse(json_str)

@csrf_exempt
def code_interpreter_sql_get_tablelayout(request: HttpRequest):
    thisFunctionName: str = sys._getframe().f_code.co_name
    if demo_mode == "True":
        print("Called "+ thisFunctionName + " in demo mode")
        res = {"status":"Error:デモモードではこの機能は利用できません。"}
    
        #json形式の文字列を生成
        json_str = json.dumps(res, ensure_ascii=False, indent=2) 
        return HttpResponse(json_str)
    else:
        print("Called "+ thisFunctionName)
        
    session_id:str = ''
    chat_text:str = ''
    schemaname:str = ""
    tablename:str = ""

    if request.method == 'POST':
        try:
            datas = json.loads(request.body)
    
            # requestには、param1,param2の変数がpostされたものとする
            pageid = datas["pageid"]
            session_id = datas['session_id']
            schemaname = datas["schemaname"]
            tablename = datas["tablename"]        

            print(pageid)
            print(session_id)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            res = {"status":"NG","data":f"入力パラメータが足りません。Error:{e}","image_url":"","data_url":"","exec_code":""}
            logger.exception('['+thisFunctionName+']Error:' + str(e))

            #json形式の文字列を生成
            json_str = json.dumps(res, ensure_ascii=False, indent=2) 
            return HttpResponse(json_str)
           
    try:
        output:str = ''
        prompt:str = ''
        sqlcode:str = ''
        df:pd.DataFrame = pd.DataFrame()
        
        # テーブルレイアウトを取得
        df = get_sql_tablehead(schemaname,tablename)
        df2 = get_sql_table_summary(schemaname,tablename)
    
        df = optimize_df_types(df) # データフレームのデータ型を最適化する
        data_head:str = df.head().to_markdown()
        data_head = data_head.replace(' 00:00:00', '')

        data_describe:str = df2.to_markdown()
        res = { "status": "OK", "datarayout": data_head,"data_describe":data_describe,"dateime_columns":"" }
                                            
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.exception('['+thisFunctionName+']Error:' + str(e) )

        res = {"status":"NG CSVが読み込めません。フォーマットを確認ください。Error:{e}"}
    
    #json形式の文字列を生成
    json_str = json.dumps(res, ensure_ascii=False, indent=2) 
    return HttpResponse(json_str)


def get_datetime_columns(df:pd.DataFrame) -> str:

    # 日付型の列を選択する
    date_cols = df.select_dtypes(include=['datetime64']).columns

    output:str = '|列名|最小|最大|\n|---|---|---|\n'

    if len(date_cols) > 0:
        for col in date_cols:
            # 最小日付と最大日付を抽出する
            min_date = df[col].min()
            max_date = df[col].max()

            # 日付の表示形式を変更する
            min_date_str = min_date.strftime('%Y/%m/%d %H:%M:%S')
            max_date_str = max_date.strftime('%Y/%m/%d %H:%M:%S')

            # min_date_strに'00:00:00'が含まれていたら空白で分割し、最初の要素を取得する
            if '00:00:00' in min_date_str:
                min_date_str = min_date_str.split(' ')[0]    
            if '00:00:00' in max_date_str:
                max_date_str = max_date_str.split(' ')[0]    

            # 結果を表示する
            output += '|' + col + '|' + min_date_str + '|' + max_date_str + '|\n'
    else:
        print('日付や日時の列はありません')
        
    return(output)


def get_from_blob_to_df(container_name:str,blob_name:str):
    # Azure Blob Storageの接続情報
    connection_string:str = azure_blob_connect_str

    # Blob Service Clientを作成する
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # コンテナーを取得する
    container_client = blob_service_client.get_container_client(container_name)

    # Blobを取得する
    blob_client = container_client.get_blob_client(blob_name)

    # Blobからファイルをダウンロードする
    with open(blob_name, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())

    # CSVファイルをpandasのデータフレームに変換する
    df = pd.read_csv(blob_name)
    
    # ファイルが存在する場合は削除する
    if os.path.exists(blob_name):
        os.remove(blob_name)
        print(f"{blob_name} を削除しました。")
    else:
        print(f"{blob_name} は存在しません。")
    
    return df

def copy_from_blob_to_blob(src_blob_name:str,src_container_name:str,dst_blob_name:str,dst_container_name:str):
    # Azure Blob Storageの接続情報
    connection_string:str = azure_blob_connect_str

    # Blob Service Clientを作成する
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # コピー元のコンテナー名とファイル名を指定する
    source_container_name = src_container_name
    source_blob_name = src_blob_name

    # コピー先のコンテナー名とファイル名を指定する
    destination_container_name = dst_container_name
    destination_blob_name = dst_blob_name

    res:str = ""
    try:
        # コピー元のBlobを取得する
        source_blob_client = blob_service_client.get_blob_client(container=source_container_name, blob=source_blob_name)

        # コピー先のBlobを作成する
        destination_blob_client = blob_service_client.get_blob_client(container=destination_container_name, blob=destination_blob_name)

        # Blobをコピーする
        destination_blob_client.start_copy_from_url(source_blob_client.url)
        
        print(f"{source_blob_name} を {destination_blob_name} にコピーしました。")
        res = "OK"
    except Exception as e:
        print(f"An error occurred: {e}")
        res = f"NG Error:{e}"
    return res
