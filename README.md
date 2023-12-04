# はじめに

## アプリのコンセプト
- 専門家を模倣する（Expert imitator）というコンセプトで画面構成されたGPT-4を利用したチャットアプリです。
- スキルが「上の上」レベルの人間のアウトプット品質には太刀打ちできないですが、「上の下程度の人間が1週間かけて作るレベルの回答」を、即時回答いたします。

## Demo url
https://tomohiku-gpt-web.azurewebsites.net/

※ デモ環境ではGPT-4との通信はできずErrorになりますが、出力例が各ページに用意されているので利用イメージがわかります。

## 機能説明ブログ
Qiita
https://qiita.com/tomohiku/items/6363e4df11f3750344db

## 言語とフレームワーク

- 言語
  - Frontend: Typescript + html + css
  - Backend: Python

- Framework
  - Web: Django

- DB
  - RDB: SQLite3 or PostgreSql
  - Vector DB: PostgreSql

- Storage
  - Azure Storage Blob

- Log
  - Azure Application Insight

※生成AI系のFramework（例えばSemantic Kernel、Langchainなど）は、部分的に部品を使っていますが、ほとんど使っていません。

## 機能

### 実装している主な機能
#### 利用シナリオ系
1. GPTと会話：最も定番機能。ただ「チャット画面の文字の見やすさ」には工夫を入れている。
2. 頁ごとのプロンプトテンプレート切替え機能：GPTsと設計思想は違うがOutputは類似する機能
3. ベクトル検索関連：PDFアップロードによる即時ベクトル化、ベクトル検索を使った回答
4. Code Interpreter：PythonおよびSQLのコード生成＆コード実行
5. AI同士の会話：AI同士のディベート、AIだけの会議など

#### 非機能系
1. ログイン認証：Django標準認証。デモアプリとしては Azure AD よりDjango標準認証の方が都合が良かったので。
2. 会話ログ：チャットでの会話のやり取りはDBに保管される
3. アプリログ：Djangoログおよび Application Ingsightに保管される。
4. スマホ・タブレット対応：iPhone,iPadは動作確認済み

### 未実装（今後実装するかも）。※Open AI Chat や Bing Chat 等の主要サービスでは実装されている
1. 頁ごとのプロンプトテンプレートの作成・編集・削除画面：GPTsの作成画面と似た作りで構想
2. 頁の共有：GPTs Storeのようなもの
3. 履歴表示＆共有：使い勝手を左右する重要な機能ではある
4. Plugin 連携：Semantic KernelのPlugin利用を真似ると実装できそう。ただ組織内でセキュアに利用するアプリという観点で考えるとPluginの必要性には疑問を感じる
5. プリセットされた指示文：初回のシステムプロンプトの調整機能
6. 「イイネ」ボタン：イイネのカウント表示は現状はダミー

# 実行のための Set up
## 事前インストールソフトウェア

- Python 3.9.7
  - Openaiのコード生成の精度に影響があるため、Versionは適切にインストールください。
  - Download page
    - https://www.python.org/downloads/release/python-397/
- Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017, 2019 and 2022
  - Download page
    - https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist?view=msvc-170


## セットアップ手順 (現状Windowsのみ手順を記載。ただし、MacやLinuxでも動作可)
1. RepositoryからClone もしくは Download し、任意のフォルダに配置
2. Powershellで配置先のフォルダに移動
```powershell
cd {{配置フォルダ}}
```
3. PythonのVersion確認
```powershell
C:\Users\{user_name}\AppData\Local\Programs\Python\Python39\python.exe --version
```
  - 3.9.7 であればOK。違っていた場合は、インストールフォルダが違っている可能性あり。
  - ※Pythonのインストールフォルダが"C:\Users\{user_name}\AppData\Local\Programs\Python\Python39\"の場合。
4. Pythonの仮想環境の作成
```powershell
C:\Users\{user_name}\AppData\Local\Programs\Python\Python39\python.exe -m venv env
```
5. 作成したpython仮想環境をアクティブにする。※環境変数を上書きする
```powershell
.\env\Scripts\Activate.ps1
```
6. 実行されているpython.exeコマンドのPathを確認。Sourceが"{配置フォルダ}\env\Scripts\python.exeになっているか確認。
```powershell
gcm python
```
7. Pythonライブラリのインストール
```powershell
pip install -r .\requirements.txt
```
8. 配置フォルダの".env.sample"をコピーして".env"として保存
9. ".env"をテキストエディターで編集。必須と任意があり、任意を入力しないと利用できない機能があります。
<details><summary>.envの内容</summary>

```python
### 必須 ###

# Demoモードを有効にするかどうか True or False
DEMO_MODE_ENABLED="False"

# 認証機能を有効にするかどうか True or False
AUTH_ENABLED="False"

# Azure Openai Services API
# このAPIを使用するためには、Azure Openai Servicesのアカウントが必要になる。
# deploy名(engine名)は、"gpt-4","gpt-32k","text-embedding-ada-002"で固定なので注意。※gpt-4 turboは未対応
# AzureのAPIのみ対応。※OpenAI社のAPIを使用したい場合はCodeの修正が必要
# Endpoint Ex:"https://demo.openai.azure.com/"
AZURE_OPENAI_ENDPOINT=""  
AZURE_OPENAI_API_KEY="==your key=="
AZURE_OPENAI_API_VERSION="2023-08-01-preview"

# DATABASE_TYPE = "POSTGRESQL" or "SQLITE3"
# SQLITE3はファイル型のDBであり、Localにデータを保存する。そのためContainerを再構成するなどファイルが消えるとデータが消去される。
# PDFのアップロードによるVector検索を使用するためには、Vector検索に対応させたPOSTGRESQLを使用する必要がある。
DATABASE_TYPE="SQLITE3"

# POSTGRESQLの場合のみ必須
# host Ex:"demo.postgres.database.azure.com"
POSTGRES_CONNECTION_HOST=""
POSTGRES_CONNECTION_USERID="==user id=="
POSTGRES_CONNECTION_PASSWORD="==your pass=="

# Django access allow hosts デプロイ先サイトのURL＆ローカル実行環境。これがないとDjangoのWebサイトにアクセスできない ローカル環境も設定が必要
# カンマ区切り.Ex:"demo1.azurewebsites.net,demo2.azurewebsites.net,127.0.0.1,*"
ALLOWED_HOSTS="127.0.0.1,*"
    
# CORS&CSRF allow hosts デプロイ先サイトのURL。これがないと、Azure App serviceでCORS and CSRFエラーが発生する
# カンマ区切り.Ex:"https://demo1.azurewebsites.net,https://demo2.azurewebsites.net"
CORS_AND_CSRF_TRUSTED_HOST=""

# Django secret key 実行時にセッション管理やパスワードのハッシュ化などに使用される。GUIDを生成して最初に一度だけ設定設定する。GUIDであればどのような文字列でも良い。
DJANGO_SECRET_KEY='a1234567-b123-c123-d123-abc123456789'

### 任意 ###

# Azure Blob Storage
# これを設定しないと、PDFのアップロードやCode interpreterが利用できない
# Account key Ex:"vuV5wXpp9XFthx93HDK84047uVeXXXX/aaaaaaaaaaaaaaaaaaaaaaaaaaa=="
AZURE_BLOB_STORAGE_ACCOUNT_KEY="==your key=="
AZURE_BLOB_STORAGE_ACCOUNT_NAME="==account name=="

# Azure Blob Storage Container
# アップロードしたPDFの配置用
AZURE_BLOB_CONTAINER_NAME_FOR_PDFUPLOAD="uploadfiles"
# Code interpreterの保存用
AZURE_BLOB_CONTAINER_NAME_FOR_CODEINTERPRETER="codeexecfiles"
# CSVのプリセット頁で使用するCSVの配置用
AZURE_BLOB_CONTAINER_NAME_FOR_CSVPRESET="preset"

# Azure Bing Search API
# これを設定しないと、Bing検索が利用できない
# URL Ex:"https://api.bing.microsoft.com/v7.0/search"
AZURE_BING_SEARCH_URL=""
AZURE_BING_SEARCH_API_KEY="==your key=="

# Azure Application Insights key
# これを設定しないと、Application Insightsでのログ収集ができない
# True or False
APPINSIGHT_ENABLED="False"
# Ex:"InstrumentationKey=;IngestionEndpoint=;https://japaneast-1.in.applicationinsights.azure.com/;LiveEndpoint=https://japaneast.livediagnostics.monitor.azure.com/"
APPINSIGHT_KEY="" 

```

</details>

10. DBの初期設定をpythonのツールで行う。1. DBの定義ファイルを作成。models.pyを読み、.\app\migrationsフォルダにセットアップ準備ファイルが作成される。
```powershell
python manage.py makemigrations
```
11. DBの初期設定をpythonのツールで行う。2. DBの定義に従ってDBのテーブル等を作成。
```powershell
python manage.py migrate
```
12. 起動
```powershell
python manage.py runserver
```

# 開発のための Set up

## 事前インストールソフトウェア

- Node.js
  - 最新版
  - Download page
    - https://nodejs.org/en/download
- Visual studio code
  - 最新版
  - Download page
    - https://code.visualstudio.com/
  - pythonをデバッグするために必要な拡張機能
    - Name: python , Author:Microsoft 

## デバッグ実行の手順
1. "{配置フォルダ}/chatgptwebapp"フォルダを Visual studio code で開く
2. views.pyを開き、F5でデバッグ実行

## Typescript をコンパイル
### 準備手順
1. powershell を開き、カレントディレクトリを "{配置フォルダ}/chatgptwebapp" にする
2. 次のコマンドでNode.jsのライブラリをインストールする。package.jsonを参照し、node_modulesフォルダにライブラリが配置される。
```powershell
npm install
```
3. typescriptのコンパイラを、グローバル引数をつけて、インストールする。
```powershell
npm install -g typescript
```
### Typescriptファイル（.ts）のコンパイル
- tsconfig.jsonが配置されている "{配置フォルダ}/chatgptwebapp"フォルダで、tsc コマンドを実行。typescript のコンパイルを行い、js ファイルとmap ファイルが作成される。
```powershell
tsc
```
5. Typescriptのコンパイル設定は、tsconfig.jsonで行っています

# Advanced Options

## 認証の有効化
### 有効化手順
.env で設定を変更する
```python
# 認証機能を有効にするかどうか True or False
AUTH_ENABLED="True"
```
### ユーザの追加方法
1. 初回はまず super userを作成する
```powershell
$ python manage.py createsuperuser
Username (leave blank to use 'xxx'): admin
Email address: xxx@xxx
Password:
Password (again):
Superuser created successfully.
```

2. userを作成する
  - admin ページで作成する。参考: https://docs.djangoproject.com/en/1.8/intro/tutorial02/
  - Django shellを使ってUserを作成する
```powershell
$ python manage.py shell
>>> import django.contrib.auth
>>> User = django.contrib.auth.get_user_model()
>>> user = User.objects.create_user(username='guest', password='guestDesu')
```

## ページの追加方法
DBにデータを保持し、OpenAIのGPTsのように画面から追加＆編集＆削除できるようにする構想であるが、現状jsonにてメンテナンス。
1. chatgptwebapp\app\static\app\html\pages.data.tsを編集する
```typescript
// 1頁を構成するデータ

//////p0101//////////////////////
{
page_id:'p0101', // 各ページのID ※重複不可
expert_name:'秘書兼翻訳家', // メニューに表示される
expert_job:'翻訳', // メニューに表示される
expert_photo:'f3.png', // メニューに表示される
iine: 409, // いいね数。カウントアップ機能は未実装であり、現状は固定で見た目のみの数値。
bingbrowseflg:'off', // Web検索機能の有効無効のデフォルト値
apiType:'regularchat', // 機能種別 ※以下で別途説明
expert_role:'[秘書兼翻訳家]:ビジネスにおける事務や調整事が得意', // 個別ページの上部に表示される説明
expert_greeting:'文章のトーンを考慮して翻訳します。ここでは社内の情報を含めても安全に翻訳ができます。', // 個別ページの上部に表示される説明
expert_firstmessage:'文章のトーン考慮して日本語を英語に翻訳をいたします。翻訳したい文を入力してください。', // 個別ページを開いた際の最初の吹出しメッセージ
// プロンプトのテンプレート 入力フィールドは {{入力}}とする
req_template: '"""\n\
{{翻訳したい文}}\n\
"""\n\
上記の文章を{{文章のトーン}}、英語に翻訳して\n\
',
// 入力フィールドの定義
req_replacewords: [
  '{{翻訳したい文}}'
  ,'{{文章のトーン}}'
],
// 入力フィールドのラベル
in_labels: [
  '翻訳したい文'
  ,'文章のトーン (例:元文のままで,ビジネスに適した文体に,カジュアルに,フォーマルに, など)'
],
// 入力フィールドの例文 ※デフォルトで入力されているデータ
in_examples: [
'XXX株式会社 YYY様\n\
\n\
始めましてAAA株式会社 BBBと申します。 \n\
\n\
拝啓、貴社ますますご盛栄のこととお慶び申し上げます。初めてのお取引となりますが、基礎工事についての見積もりをご依頼させていただきたいと存じます。勝手ながら迅速な対応をお願いしておりますので、依頼手続きや連絡先をお知らせいただけますと幸いです。何卒、宜しくお願い申し上げます。'
, '始めて連絡する発注先に送るように丁寧な文体で'
],
// 出力例
out_example: 'Dear YYY, XXX Corporation,\n\n\
Greetings, I am BBB from AAA Corporation. \n\n\
I hope this message finds your company in prosperous times. This will be our first transaction together. I am reaching out with the intention of requesting a quote for the foundational work that we are planning. Given the urgency of our needs, we would greatly appreciate if you could provide information about the necessary procedures and the relevant contacts as soon as possible.\n\
We look forward to establishing a business relationship with you. Thank you very much for your kind attention and cooperation. \n\
\n\
Best regards,\n\
\n\
BBB,\n\
AAA Corporation',
},
```

  - apiType
    - 8 種類
      - regularchat: プロンプトを会話形式で行う通常パターン
      - Meeting: Meeting形式でプロンプトが自動投入されるパターン
      - Debate: ディベート形式でプロンプトが自動投入されるパターン
      - fileupload: ベクトル検索のためにPDFアップロードするページのパターン
      - search: ベクトル検索を実行するパターン
      - Codeinterpreter: PythonのCode Interpreterを実行するパターン
      - Codeinterpreter_Preset: PythonのCode Interpreterを事前Preset済みのCSVで行うパターン
      - Codeinterpreter_Sql: SQLのCode Interpreterを実行するパターン

2. 上記で書いたtypescriptのコンパイル手順でコンパイルする


## Vector検索を使った機能の有効化手順

大きく分けて、２つの用意が必要です。
① PostgreSQLデータベースの用意
② Azure Storage Blob の用意

### ① PostgreSQLデータベースの用意
1. PostgreSQLの環境を用意する。Vector Extensionの対応しているVersionを用意してください。
  - 例えば、Azure Database for PostgreSQL のフレキシブル サーバー Version:15.3
2. PostgreSQLのExtensionを有効化する
  - 本実装で使うExtensionは"pgvector"と"uuid-ossp"の2つ
```SQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
```
3. .envでDBをPostgreSQLにする
```python
# DATABASE_TYPE = "POSTGRESQL" or "SQLITE3"
# SQLITE3はファイル型のDBであり、Localにデータを保存する。そのためContainerを再構成するなどファイルが消えるとデータが消去される。
# PDFのアップロードによるVector検索を使用するためには、Vector検索に対応させたPOSTGRESQLを使用する必要がある。
DATABASE_TYPE="POSTGRESQL"

# POSTGRESQLの場合のみ必須
# host Ex:"demo.postgres.database.azure.com"
POSTGRES_CONNECTION_HOST=""
POSTGRES_CONNECTION_USERID="==user id=="
POSTGRES_CONNECTION_PASSWORD="==your pass=="
```

4. DBの初期設定をpythonのツールで行う。1. DBの定義ファイルを作成。models.pyを読み、.\app\migrationsフォルダにセットアップ準備ファイルが作成される。
```powershell
python manage.py makemigrations
```
5. DBの初期設定をpythonのツールで行う。2. DBの定義に従ってDBのテーブル等を作成。
```powershell
python manage.py migrate
```
PostgreSQLの対象のSchemaにテーブルが作成されていればOK

### ② Azure Storage Blob の用意

1. Azure Storage アカウントを作成し、Account名とKeyを取得する
2. 作成したBlob Storageに.env内で設定したContainer名の3つのContainerを作成する
3. .envに設定をする
```python
# Azure Blob Storage
# これを設定しないと、PDFのアップロードやCode interpreterが利用できない
# Account key Ex:"vuV5wXpp9XFthx93HDK84047uVeXXXX/aaaaaaaaaaaaaaaaaaaaaaaaaaa=="
AZURE_BLOB_STORAGE_ACCOUNT_KEY="==your key=="
AZURE_BLOB_STORAGE_ACCOUNT_NAME="==account name=="

# Azure Blob Storage Container
# アップロードしたPDFの配置用
AZURE_BLOB_CONTAINER_NAME_FOR_PDFUPLOAD="uploadfiles"
# Code interpreterの保存用
AZURE_BLOB_CONTAINER_NAME_FOR_CODEINTERPRETER="codeexecfiles"
# CSVのプリセット頁で使用するCSVの配置用
AZURE_BLOB_CONTAINER_NAME_FOR_CSVPRESET="preset"
```

## Code Interpreterを使った機能の有効化手順
- 「Vector検索を使った機能の有効化手順」が終わっていること。
‐ Code Interpreter機能では、PostgreSQLとAzure Storageが必要。

### Pythonのコード生成

1. CSVを随時アップロードするCode InterpreterはPostgreSQLとAzure Storageが設定されていれば利用可能

2. CSVプリセット型の機能は、Azure Storage blob へプレセットするCSVの配置が必要

  - プリセットするCSVデータ："\chatgptwebapp\app\static\app\sample_csv\p1301.csv" 
  - Blob Containerの"preset"にアップロードする

### SQLのコード生成
#### SQLのコード生成を使ったサンプルページためのPostgreSQLテーブルのデータ追加
[視聴率アナリスト] → [視聴率データの加工＆抽出(Sql)]を使うためには、PostgreSQLにテーブルを追加し、データをセットしてください。

- テーブルのImportするサンプルデータ
"\chatgptwebapp\app\static\app\sample_csv\p1302_import2postgresql.csv"

- PostgreSQLのCSVインポートコマンド

```sql
\copy public.salesamount FROM 'C:/dev/temp/import.csv' DELIMITER ',' CSV HEADER ENCODING 'UTF8';
```

- 使用するテーブル名の指定方法
  - ファイル名
    - chatgptwebapp\app\static\app\html\pages_data.ts
 
```typescript
interface tableinfo {
    page_id: string;
    table_schema: string;
    table_name:string;
}
export let tableinfo_list: tableinfo[] = [
{ 
    page_id: 'p1302',
    table_schema: 'public',
    table_name: 'salesamount'
}
```

- プロンプトカタログの追加方法
  - ファイル名
    - chatgptwebapp\app\static\app\html\pages_data.ts

```typescript
interface catalogdata {
    page_id: string;
    title: string;
    prompt:string;
    created_date: string;
}
// 視聴率データの加工＆抽出のためのカタログリスト
export let catalog_list: catalogdata[] = [
{ 
page_id: 'p1302',
title: '期間内で社員名別の月単位売上金額の合計',
prompt: `
## 抽出条件
- 売上年月日が2011/5/01から2012/8/31まで。

## グルーピング
- 売上年月日：年月単位でグルーピング
- 社員名
- 部門名
- 担当エリア

## 抽出列＆フォーマット＆順番。指定した列を指定したフォーマットで、上から順番で表にしてください。
- 売上年月
- 社員名
- 部門名
- 担当エリア
- 売上金額の合計

## 並び順
- 売上金額:降順
`
, created_date: '2023/09/30' },
];

```


## インターネット検索情報（Bing Search）を使った機能の有効化手順
Azureで Bing Search を作成し、Azure Bing Search APIを利用できるようにする。
URLとAPI Keyを取得し、.env で次の設定を変更する
```python
AZURE_BING_SEARCH_URL="" #Ex:"https://api.bing.microsoft.com/v7.0/search"
AZURE_BING_SEARCH_API_KEY="==your key=="
```

## Webアプリログの統合管理（Application Insight）を使った機能の有効化手順
Azureで Application Insight を作成する。
プロパティのページで、接続文字列を取得する。

.env で設定を変更する
```python
# Azure Application Insights key
# これを設定しないと、Application Insightsでのログ収集ができない
# True or False
APPINSIGHT_ENABLED="True"
# Ex:"InstrumentationKey=;IngestionEndpoint=;https://japaneast-1.in.applicationinsights.azure.com/;LiveEndpoint=https://japaneast.livediagnostics.monitor.azure.com/"
APPINSIGHT_KEY="" 
```

## デモモード

.env で設定を変更する
```python
# Demoモードを有効にするかどうか True or False
DEMO_MODE_ENABLED="True"
```

# その他
- ImageフォルダにImageはすべてDALL·Eで作成したものです。
- よろしければStarをつけてもらえると励みになります。
