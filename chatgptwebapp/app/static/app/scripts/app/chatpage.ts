/// <reference path="../../../../../node_modules/@types/jquery/index.d.ts" />
/// <reference path="../../../../../node_modules/@types/marked/index.d.ts" />
import { data, error } from 'jquery';
import {pageData, catalog_list, tableinfo_list} from '../../html/pages_data.js';

/////////////////////////////////////////
// Main
/////////////////////////////////////////
const image_path:string = 'static/app/images/';
let chatpage:string = "p0000"; // 初回に開くページ
let apiType:string = "chatGPT"; // 初回に開くページのapiType
let now_session_id:number = 0; // 現在の会話ID
let now_session_data:Array<session_data> = []; // 現在会話画面における会話履歴データ
let debate_stage:number = 1; // ディベートのステージ

// DOMが読み込み後の関数 $(document).ready(function(){}の新しい書き方
$(function(){
    create_plist();
    chatui_loadpage(chatpage);

    // Demo modeの時は、タイトルにDemo modeを追加する ※手動でコメントアウトする必要あり
    // $('#app_tittle').html('Expert Imitator <span style="font-size:10px;background-color:darkblue;">Demo mode</span>');
    
    // クリックされたタブにactiveクラスを追加
    $('#'+chatpage).addClass("active");
});

$(window).on('load', function() {
    resizeWindow();

    // @ts-ignore
    marked.use({
        // async: true,
        // pedantic: false,
        gfm: true,
        headerIds: false,
        mangle: false,
    });

    // markdownに脚注がある場合は、以下のコードを追加する marked.jsでは脚注が対応できない 例：[^1]:注釈の内容
    // // @ts-ignore
    // mdit = markdownit();
    // var result = mdit.render('# markdown-it rulezz!\n\nテキスト[^1]\n\n[^1]:注釈の内容\n');
    // console.log(result);

    $('#send_button').prop('disabled', true);
    $('#stop_button').hide();

});

function create_plist(){
    let plist_html = '';
    let lanpOnOff = '';
    for (let k = 0; k < pageData.length; k++) {
        plist_html = '\
        <li id="@@p1@@" class="clearfix">\
            <img src="@@p2@@" alt="avatar">\
            <button type="button" class="btn btn-secondary iine_badge disabled">\
                👍 <span class="badge bg-secondary iine_badge_num">@@p3@@</span><span class="visually-hidden iine_badge_num">unread messages</span>\
            </button>\
            <div class="about">\
                <div class="name">@@p4@@</div>\
                <div class="status"> <i class="fa fa-circle @@p5@@"></i> @@p6@@ </div>\
            </div>\
        </li>'

        plist_html = plist_html.replace(/@@p1@@/g, pageData[k].page_id);
        plist_html = plist_html.replace(/@@p2@@/g, image_path + pageData[k].expert_photo );
        plist_html = plist_html.replace(/@@p3@@/g, pageData[k].iine.toString());
        plist_html = plist_html.replace(/@@p4@@/g, pageData[k].expert_job);

        if(pageData[k].apiType !== ''){
            lanpOnOff = 'online';
        }else{
            lanpOnOff = 'offline';
        }
        plist_html = plist_html.replace(/@@p5@@/g, lanpOnOff);
        plist_html = plist_html.replace(/@@p6@@/g, pageData[k].expert_name);


        $('#plistul').append(plist_html);
    }
}

/////////////////////////////////////////
// Event
/////////////////////////////////////////

window.onresize = resizeWindow;
const whileTypingCharactor:string = '<span id="cursor"></span>&nbsp;';

// 左部のメニュークリックイベント
$(function(){
    $('#plist li').on('click', function(){
        chatui_loadpage(this.id);

        // すべてのタブからactiveクラスを削除
        $('#plist li').removeClass("active");
        // クリックされたタブにactiveクラスを追加
        $(this).addClass("active");
    });
});

function chatui_loadpage(page:string):void{

    chatpage = page; //現在開いているページ設定
    
    // 現在開いているページのapiTypeを設定
    for (let k = 0; k < pageData.length; k++) {
        if (pageData[k].apiType !== '') {                    
            if (pageData[k].page_id === chatpage) {
                apiType = pageData[k].apiType;
            }
        }
    }

    let chatpagehtmlfile:string = '';
    // p0000はChatGPTの自由チャットでレイアウトが別なので分岐
    switch (apiType) {
        case 'chatGPT':
        case 'fileupload':
        case 'search':
        case 'CodeInterpreter':
        case 'Debate':
        case 'Meeting':
                chatpagehtmlfile = chatpage;
            break;
        case 'CodeInterpreter_Preset':
            chatpagehtmlfile = 'p9998';
            break;
        case 'CodeInterpreter_Sql':
            chatpagehtmlfile = 'p9997';
            break;
        default:
            chatpagehtmlfile = 'p9999';
            break;
    }
    
    // Mainページの読み込み
    let chatpagehtml:string = '../static/app/html/chatui_' + chatpagehtmlfile + '.html'
    $('#chatui-pp').load(chatpagehtml, function(){
        resizeWindow();
        now_session_data = [];
        // 会話IDを初期化
        now_session_id = 0;

        $('.ai-photo').attr('src', 'static/app/images/ai.png');
        $('.me-photo').attr('src', 'static/app/images/me.png');

        switch (chatpage) {
            case 'p0000':
                for (let k = 0; k < pageData.length; k++) {
                    if (pageData[k].page_id === chatpage) {
                        $('#expert-photo').attr('src', image_path + pageData[k].expert_photo);
                        $('#expert-role').text(pageData[k].expert_role);
                        $('#expert-greeting').text(pageData[k].expert_greeting);

                        $('#inputtextarea').prop('disabled', false);
                        $('#browseflg').val(pageData[k].bingbrowseflg);
                        $('#browseflg').prop('disabled', false);
                        $('#browseflg').trigger('onchange');
                    }
                }
                break;
            default:
                let existpageflg = false;
                for (let k = 0; k < pageData.length; k++) {
                    if (pageData[k].apiType !== '') {
                        if (pageData[k].page_id === chatpage) {
                            existpageflg = true;

                            if (apiType == 'CodeInterpreter_Preset' || apiType == 'CodeInterpreter_Sql') {
                                let in_label_and_textare = '';
                                for (let i = 0; i < pageData[k].in_labels.length; i++) {
                                    in_label_and_textare += pageData[k].in_labels[i];    
                                }
                                $('#in_label_and_textare').html(in_label_and_textare);
                            }else{
                                let in_label_and_textare = '';
                                for (let i = 0; i < pageData[k].in_labels.length; i++) {
                                    in_label_and_textare += pageData[k].in_labels[i]+':'+'<textarea id="textarea'+(i+1)+'" class="form-control form-textarea me-textarea" placeholder="例：' + pageData[k].in_examples[i] + '" oninput="textarea_Output(this)">' + pageData[k].in_examples[i] +'</textarea>';
    
                                }

                                $('#in_label_and_textare').html(in_label_and_textare);
                                for (let i = 0; i < pageData[k].in_examples.length; i++) {
                                    $('#textarea'+ (i+1)).trigger('oninput');
                                }
                            }

                            $('#expert-photo').attr('src', image_path + pageData[k].expert_photo);
                            $('#expert-role').text(pageData[k].expert_role);
                            $('#expert-greeting').text(pageData[k].expert_greeting);
                            $('#expert_firstmessage').html(pageData[k].expert_firstmessage);

                            if (apiType !== 'Debate' && apiType !== 'Meeting') {
                                // @ts-ignore
                                $('#outmessege').html(marked.parse(pageData[k].out_example));
                            } else {
                                // ディベートの場合は、ディベートのカウントを初期化する
                                debate_stage = 1;
                            }
                            $('#browseflg').val(pageData[k].bingbrowseflg);
                        }
                    }
                }

                // #expert-roleが空の場合は、ページが存在しないので、エラーを表示する
                if(existpageflg){
                    $('#inputtextarea').prop('disabled', true);
                    $('#browseflg').prop('disabled', true);
                    $('#browseflg').trigger('onchange');
                }else{
                    alert('未作成。赤いランプはまだ作成していません。');
                }

                break;
        }

        // 【追加】個別機能を持つ画面の場合は、ここで個別の処理を行う
        if (apiType == 'search') {

            getlist_of_registered_document().then(data => {
                let list_of_registered_document:Array<getlist_of_registered_documentModel> = data;
                let option_html = '';

                for (let i = 0; i < list_of_registered_document.length; i++) {
                    option_html += '<option value="' + data[i].document_filename + '">' + data[i].document_name + '</option>';
                }
                // console.log(data);
                let insert_html = '<select multiple="multiple" id="multiselect" name="multiselect">'+ option_html + '</select>'
                $('#multiselectdiv').html(insert_html);

                for (let k = 0; k < pageData.length; k++) {
                    if (pageData[k].apiType !== '') {                    
                        if (pageData[k].page_id === chatpage) {
                            let selectfilename = pageData[k].in_examples[1]
                            $('#multiselect option[value="' + selectfilename + '"]').attr('selected', 'selected');
                        }
                    }
                }

                // @ts-ignore
                $('#multiselect').multipleSelect({
                    width: '100%',
                    formatSelectAll: function() {
                        return 'すべて';
                    },
                    formatAllSelected: function() {
                        return '全て選択されています';
                    }
                },
                );

                // modalの中身を作成
                // header
                $('#otherModalLabel').text('登録資料の内容');
                // body
                let modal_html: string = "";
                for (let i = 0; i < list_of_registered_document.length; i++) {
                    modal_html += '<div class="card-document text-bg-light">\
                                <div class="card-header ">'+ data[i].document_filename + '</div>\
                                <div class="card-body text-dark ">\
                                    <h5 class="card-title">'+ data[i].document_name + '</h5>\
                                    <p class="card-text">'+ data[i].discription + '</p>\
                                    <a href="'+ data[i].document_url + '" target="_blank" rel="noopener noreferrer" class="btn btn-link">Download</a>\
                                </div>\
                                <time class="card__time card__item small" datetime="2021-12-01">登録日:'+ data[i].create_timestamp + '</time>\
                            </div>'
                }

                modal_html = '<section class="container-document">\
                <div class="container-document__wrapper" id="document-list">'
                + modal_html                
                + '</div></section>>';
                $('#modal-other-body-id').html(modal_html);

            });
        }else if(apiType == 'Debate' || apiType == 'Meeting'){
            
                // modalの中身を作成
                // header
                $('#otherModalLabel').text('職能一覧');
                // body
                let modal_html: string = "";
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">サービス部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">企画部の部長</h5>\
                            <p class="card-text">新規サービスの企画を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                    <div class="card-header ">サービス部門</div>\
                    <div class="card-body text-dark ">\
                        <h5 class="card-title">営業部の部長</h5>\
                        <p class="card-text">サービスの営業を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                    </div>\
                    <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                </div>'
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">サービス部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">開発部の部長</h5>\
                            <p class="card-text">新規サービスの開発を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                    <div class="card-header ">サービス部門</div>\
                    <div class="card-body text-dark ">\
                        <h5 class="card-title">運用部の部長</h5>\
                        <p class="card-text">サービスの運用を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                    </div>\
                    <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                </div>'
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">コンサルサービス部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">ITコンサルタント</h5>\
                            <p class="card-text">ITコンサルティングサービスを提供するベテラン社員。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                    <div class="card-header ">コンサルサービス部門</div>\
                    <div class="card-body text-dark ">\
                        <h5 class="card-title">ITアーキテクト</h5>\
                        <p class="card-text">サービス営業の支援およびITコンサルティングサービスの支援を提供するベテラン社員。</p>\
                    </div>\
                    <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                    <div class="card-header ">コンサルサービス部門</div>\
                    <div class="card-body text-dark ">\
                        <h5 class="card-title">UI/UXデザイナー</h5>\
                        <p class="card-text">ITコンサルティングサービスの中でもUI/UXデザインに特に特化した専門性を持つベテラン社員。</p>\
                    </div>\
                    <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'

                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">本社機能部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">法務部の部長</h5>\
                            <p class="card-text">法務を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">本社機能部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">人事部の部長</h5>\
                            <p class="card-text">人事を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">本社機能部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">経理部の部長</h5>\
                            <p class="card-text">経理を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
                modal_html += '<div class="card-document text-bg-light">\
                        <div class="card-header ">本社機能部門</div>\
                        <div class="card-body text-dark ">\
                            <h5 class="card-title">調達部の部長</h5>\
                            <p class="card-text">調達を行う部門のベテラン社員。また、部門の人的リソースの管理者。</p>\
                        </div>\
                        <time class="card__time card__item small" datetime="2021-12-01">登録日:2023/10/01 11:11:11</time>\
                    </div>'
    

                modal_html = '<section class="container-document">\
                <div class="container-document__wrapper" id="document-list">'
                + modal_html                
                + '</div></section>';
                $('#modal-other-body-id').html(modal_html);
        }else{
            // modalの中身を作成
            // header
            $('#promptModalLabel').text('AIへの問い合わせプロンプト全文');
            // body
            let modal_html: string = '<button class="btn btn-success btn-sm" onclick="chat_Button_Click(\'modal_input\')" style="margin-bottom:10px;width:100%;" data-bs-dismiss="modal" aria-label="Close">このプロンプトを使う</button>\
            <textarea id="prompt_text" class="form-control" aria-label="With textarea" style="width:100%;max-width:100%;height:90%;"></textarea>';
            
            $('#modal-body-id').html(modal_html);
        }
        
        // 該当のデータのテーブルレイアウトの取得
        if(apiType == 'CodeInterpreter_Preset'){
            postCsvFileuploadHttpResponse(null,chatpage + ".csv",get_convId());
        }else if(apiType == 'CodeInterpreter_Sql'){
            postGetSqlTableHeadHttpResponse(get_convId());
        }

        // catalog modalの中身を作成
        // header
        $('#catalogModalLabel').text('プロンプトカタログ');
        // body
        let modal_html: string = '';
        for (let k = 0; k < catalog_list.length; k++) {
            if (catalog_list[k].page_id === chatpage) {
                modal_html += `
                <details style="margin-bottom:10px;">
                <summary><span class="summary_inner"><span>@@created_date@@ : @@title@@</span><span class="summary_icon"></span></span></summary>
                <div class="summary_content">
                <button class="btn btn-success btn-sm" onclick="catalog_Button_Click(@@itemCount@@)" style="margin-top:10px;">チャットへコピー</button>
                <textarea class="form-control" id="catalog-input-@@itemCount@@" aria-label="With textarea" style="width:100%;max-width:100%;min-height:600px;">
                @@prompt@@
                </textarea>
                </div>
                </details>
                `            
                modal_html = modal_html.replace(/@@title@@/g, catalog_list[k].title);
                modal_html = modal_html.replace(/@@prompt@@/g, catalog_list[k].prompt);
                modal_html = modal_html.replace(/@@created_date@@/g, catalog_list[k].created_date);
                modal_html = modal_html.replace(/@@itemCount@@/g, k.toString());
            }
        }
        $('#modal-catalog-body-id').html(modal_html);

        // ボタンのスピンは初期状態は消しておく
        $('#chat_button_spin').hide();
        // id="promptModal"にheightを設定 これがないとモーダルがずれる
        // $('#promptModal').css('height', "auto");

        $('#inputtextarea').css('height', "60px");
        $('#inputtextarea').val('');
        $('#send_button').prop('disabled', true);


        // $('#browseflg').prop('disabled', false);
        // $('#browseflg').css('background-color', "white");
       
        // codeの色分けhighlight用
        // @ts-ignore
        hljs.highlightAll();

        const windowwidth:number = $(window).width() ?? 0;
        if (windowwidth < 1400){
            $('.chat-app .people-list').hide();
            // $('.chat-app .chat').css("margin-left","0px");
        }

      });
}

globalThis.chat_Button_Click = (e):void =>{
    console.log('chat_button click');

    $('#chat_button_spin').show();
    $('#chat_button').prop("disabled", true);
    $('#edit_button').prop("disabled", true);

    $('#outputdiv').remove();

    // testDataListから 特定の値を取得する
    let querydata:string = "";
    let searchflg:string = "off"; // デフォルトは検索オフ

    searchflg = $('#browseflg')?.val()?.toString() ?? 'off';

    $('#inputtextarea').val('');
    $('#inputtextarea').css('height', "60px");

    let htmltext:string = '<div class="clearfix li-option me-balloon"><div class="message-data smartphone-display"><img src="static/app/images/me.png" alt="avatar"></div><div class="message other-message-input smartphone-padding">@@displaytext@@</div></div>';

    // プロンプトの生成処理
    for (let k = 0; k < pageData.length; k++) {
        if (pageData[k].page_id === chatpage) {
            // apiType = pageData[k].apiType;

            if(apiType === "summary"){
                // サマリーの場合は、テキストエリアの内容をそのまま送信する
                for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                    querydata = $('#textarea'+(i+1)).val()?.toString() ?? '';
                }

                postStreamingChatGptResponse(querydata,get_convId(),apiType,searchflg); // ChatGPTに直接送信
            }else if(apiType === "fileupload"){
                // fileuploadの場合は、Formsにセットするしてそのまま送信する
                const document_name:string = $('#textarea1').val()?.toString() ?? '';
                const description:string = $('#textarea2').val()?.toString() ?? '';
                const inputElement = document.querySelector('#formFileSm') as HTMLInputElement;
                const uploadfile:File|null = inputElement.files?.[0] ?? null;

                let errorflg:boolean = false;
                // document_name, discriptionの文字数チェック
                if(document_name.length > 50){
                    alert('資料タイトルを50文字以内で入力してください');
                    errorflg = true;
                }
                if(document_name.length == 0){
                    alert('資料タイトルを入力してください');
                    errorflg = true;
                }

                if(description.length > 200){
                    alert('概要説明は200文字以内で入力してください');
                    errorflg = true;
                }
                if(description.length == 0){
                    alert('概要説明を入力してください');
                    errorflg = true;
                }
                if(uploadfile == null){
                    alert('ファイルを選択してください');
                    errorflg = true;
                }
                console.log("uploadfile name"+uploadfile?.name.slice(-4));
                if(uploadfile?.name.slice(-4) !== ".pdf"){                    
                    alert('PDFファイルを選択してください');
                    errorflg = true;
                }


                // errorflgがfalseの場合は、送信処理を実施する
                if(!errorflg){
                    postPdfFileuploadHttpResponse(document_name,description,uploadfile,get_convId()); // ChatGPTに直接送信
                    $('#formFileSm').prop('disabled', true);
                }else{
                    $('#chat_button_spin').hide();
                    $('#chat_button').prop("disabled", false);
                }
            }else if(apiType === "CodeInterpreter"){ //'CodeInterpreter_Preset'と'CodeInterpreter_Sql'はChatボタンが無いので、ここは通らない
                // fileuploadの場合は、Formsにセットするしてそのまま送信する
                const inputElement = document.querySelector('#formFileSm') as HTMLInputElement;
                const uploadfile:File|null = inputElement.files?.[0] ?? null;

                let errorflg:boolean = false;

                if(uploadfile == null){
                    alert('ファイルを選択してください');
                    errorflg = true;
                }
                console.log("uploadfile name"+uploadfile?.name.slice(-4));
                if(uploadfile?.name.slice(-4) !== ".csv"){                    
                    alert('CSVファイルを選択してください');
                    errorflg = true;
                }

                // errorflgがfalseの場合は、送信処理を実施する
                if(!errorflg){
                    postCsvFileuploadHttpResponse(uploadfile,"",get_convId());

                    $('#formFileSm').prop('disabled', true);
                }else{
                    $('#chat_button_spin').hide();
                    $('#chat_button').prop("disabled", false);
                }
            }else if(apiType === "search"){
                // 以下のコードでDisableに変えると、Enableに戻せない。コードを調査する必要あり
                // // @ts-ignore
                // $('#multiselect').multipleSelect({
                //     width: '100%',
                //     formatSelectAll: function() {
                //         return 'すべて';
                //     },
                //     formatAllSelected: function() {
                //         return '全て選択されています';
                //     },
                //     disabled: true,
                // },
                // );

                $('#textarea1').prop("disabled", true);

                querydata = pageData[k].req_template;
                for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                    querydata = querydata.replace(pageData[k].req_replacewords[i], $('#textarea'+(i+1)).val()?.toString() ?? '');
                }
                postStreamingChatGptResponse(querydata,get_convId(),apiType,searchflg); // ChatGPTに直接送信

            }else if(apiType === "Debate" || apiType === "Meeting"){

                if ( e != "modal_input" ) {
                    querydata = pageData[k].req_template;
                    for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                        querydata = querydata.replace(pageData[k].req_replacewords[i], $('#textarea'+(i+1)).val()?.toString() ?? '');
                    }
                }else{

                    querydata = $('#prompt_text').val()?.toString() ?? '';

                    for (let i = 0; i < pageData[k].in_examples.length; i++) {
                        $('#textarea'+ (i+1)).prop('disabled', true);
                    }
                    htmltext = htmltext.replace(/@@displaytext@@/g, querydata);
                    $('#chatul').append(htmltext);

                }
                debateControl(querydata,apiType,searchflg); // ChatGPTに直接送信
            
            }else{ // 通常のチャットの場合
                if ( e != "modal_input" ) {
                    querydata = pageData[k].req_template;
                    for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                        querydata = querydata.replace(pageData[k].req_replacewords[i], $('#textarea'+(i+1)).val()?.toString() ?? '');
                    }
                }else{
                    querydata = $('#prompt_text').val()?.toString() ?? '';

                    for (let i = 0; i < pageData[k].in_examples.length; i++) {
                        $('#textarea'+ (i+1)).prop('disabled', true);
                    }
                    htmltext = htmltext.replace(/@@displaytext@@/g, querydata);
                    $('#chatul').append(htmltext);
                }
                postStreamingChatGptResponse(querydata,get_convId(),apiType,searchflg); // ChatGPTに直接送信
            }

            // 印刷用に入力エリアのHTMLを書き換える
            for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                let temptext:string = $('#textarea'+(i+1)).val()?.toString() ?? '';
                $('#textarea'+(i+1)).html(temptext);
            }
        }
    }


}

globalThis.clear_Button_Click = (e):void =>{
    console.log('clear_button click');

    $('.ai-balloon').remove();
    $('.me-balloon').remove();

    $('#textarea1').val('');
    $('#textarea2').val('');
    $('#textarea3').val('');
    $('#textarea4').val('');

    // Chat履歴を削除
    now_session_data = [];

    $('#browseflg').prop('disabled', false);
    $('#browseflg').css('background-color', "white");
    $('#inputtextarea').css('height', "60px");
    $('#inputtextarea').val('');
    $('#send_button').prop('disabled', true);
    $('#chat_button_spin').hide();
    $('#chat_button').prop("disabled", false);
    $('#edit_button').prop("disabled", false);

    for (let k = 0; k < pageData.length; k++) {
        if (pageData[k].page_id === chatpage) {
            for (let i = 0; i < pageData[k].in_examples.length; i++) {
                $('#textarea'+ (i+1)).prop('disabled', false);
            }
        }
    }

    switch (apiType) {
        case 'chatGPT':
            break;
        case 'CodeInterpreter':
        case 'CodeInterpreter_Preset':
        case 'CodeInterpreter_Sql':
            $('#formFileSm').val('');
            $('#formFileSm').prop('disabled', false);
            $('#inputtextarea').prop('disabled', true);
            $('#browseflg').prop('disabled', true);
            $('#browseflg').trigger('onchange');
            break;
        case 'search':
            $('#textarea1').prop("disabled", false);

            $('#inputtextarea').prop('disabled', true);
            $('#browseflg').prop('disabled', true);
            $('#browseflg').trigger('onchange');            
        default:
            $('#inputtextarea').prop('disabled', true);
            $('#browseflg').prop('disabled', true);
            $('#browseflg').trigger('onchange');
        break;
    }

    now_session_id = 0;
}

globalThis.sse_Close_Button_Click = (e):void =>{
    sse.close();
    sse2.close();
}

globalThis.print_Button_Click = (e):void =>{
    printDiv('chatui-pp');
}

globalThis.edit_Button_Click = (e):void =>{
    console.log('edit_button click');

    for (let k = 0; k < pageData.length; k++) {
        if (pageData[k].page_id === chatpage) {
            let prompt_text:string = pageData[k].req_template;
            for (let i = 0; i < pageData[k].req_replacewords.length; i++) {
                prompt_text = prompt_text.replace(pageData[k].req_replacewords[i], $('#textarea'+(i+1)).val()?.toString() ?? '');
            }
            $('#prompt_text').val(prompt_text);
            // $('#prompt_text').val(pageData[k].req_template);
        }
    }
}

globalThis.menuopen_Button_Click = (e):void =>{
    console.log('menuopen_button click');

    if($('.chat-app .people-list').css('display') == 'none'){
        $('.chat-app .people-list').show();
    }else{
        $('.chat-app .people-list').hide();
    }
}

globalThis.input_Textarea_Button_Click = (e):void =>{
    console.log('input_textarea_button click');

    debate_stage = 9999;

    let inputText:string = $('#inputtextarea').val()?.toString() ?? '';

    var $myList = $('#chatul');
    $myList.append('<div class="clearfix li-option me-balloon"><div class="message-data smartphone-display"><img src="static/app/images/me.png" alt="avatar"></div><div class="message other-message-input smartphone-padding">'+ inputText + '</div></div>');

    $('#inputtextarea').trigger( "blur" );
    $('#inputtextarea').trigger( "focus" );
    $('#inputtextarea').val("");
    $('#inputtextarea').css('height', "60px");
    $('#send_button').prop('disabled', true);

    let searchflg:string = $('#browseflg')?.val()?.toString() ?? '';
    $('#browseflg').prop('disabled', true);
    $('#browseflg').css('background-color', "whitesmoke");

    // let apiType:string = "";
    // for (let k = 0; k < pageData.length; k++) {
    //     if (pageData[k].apiType !== '') {                    
    //         if (pageData[k].page_id === chatpage) {
    //             apiType = pageData[k].apiType;
    //         }
    //     }
    // }


    switch (apiType) {
        case 'CodeInterpreter':
        case 'CodeInterpreter_Preset':
        case 'CodeInterpreter_Sql':
                postCodeInterpreterResponse(inputText,get_convId(),apiType); // ChatGPTに直接送信
            break;
        default:
            postStreamingChatGptResponse(inputText,get_convId(),apiType,searchflg); // ChatGPTに直接送信bingsearch
            break;
    }
}

globalThis.detail_Button_Click = (e):void =>{
    console.log('detail_Button_Click click');

    let select_option_list = $('#multiselect').val();
    // alert("value=" + r );
}

globalThis.catalog_Button_Click = (e):void =>{
    console.log('catalog_Button_Click click');
    let row_count:string = e;
    let inputText:string = $('#catalog-input-'+row_count).val()?.toString() ?? '';
    $('#inputtextarea').val(inputText.trim());
    $('#inputtextarea').css('height', "500px");
    $('#send_button').prop('disabled', false);

    // モーダルを非表示にする
    // @ts-ignore
    $('#catalogModal').modal('hide'); 
}

// keydownだとコピペで値が反映されないので、keyupに変更
$("#inputtextarea").on("keyup", function(e) {
    inputtextareacommon(e);
});

$("#inputtextarea").on("keyup", function(e) {
    if (e.keyCode == 13) { // Enterが押された
        if (e.shiftKey) { // Shiftキーも押された
            // 改行を挿入
        }else { // Shiftキーは押されていない   
            let inputTemp:string = $('#inputtextarea').val()?.toString() ?? ''; 
            if(inputTemp.trim() !== ''){
                $('#inputtextarea').css('height', "60px");
                $('#inputtextarea').val('');
            }
        };    
    }
});

$("#inputtextarea").on("change",function(e)  {
});


function inputtextareacommon(e):void{
    if(e.target.textLength >= 3 ){
        $('#send_button').prop('disabled', false);
    }else{
        $('#send_button').prop('disabled', true);
    }

    if( e.target.textLength >= 3 ){
        if (e.keyCode == 13) { // Enterが押された
            if (e.shiftKey) { // Shiftキーも押された
                // 改行を挿入
            }else { // Shiftキーは押されていない   
                let inputTemp:string = $('#inputtextarea').val()?.toString() ?? ''; 
                if(inputTemp.trim() !== ''){
                    $( "#send_button" ).trigger( "click" ); 

                    // 1秒後に値をクリア※Enterキーでの改行を防ぐ
                    setTimeout(function(){
                        $('#inputtextarea').val("");
                        $('#inputtextarea').css('height', "60px");
                    }, 300);
                }
            };
        } 
    }
}

globalThis.textarea_Output = (e):void =>{
    //- 改行に合わせてテキストエリアのサイズ変更

    // textareaタグを全て取得
    const e_id = $(e).attr('id') ?? "";
    // console.log("oninput:" + e_id);
    textarea_resize(e_id);
}

function textarea_resize(id:string):void{
    //- 改行に合わせてテキストエリアのサイズ変更
    // textareaタグを全て取得
    const textareaEls = document.querySelectorAll(`#${id}`);

    let scrollHeightnum = 0
    textareaEls.forEach((textareaEl) => {
        scrollHeightnum = textareaEl.scrollHeight;
    });

    $(`#${id}`).css('height', (scrollHeightnum).toString() + 'px');

}

globalThis.changeColor = (e):void =>{
    var selectedValue = e.value;
    var backgroundColor = "";
  
    if($('#browseflg').prop('disabled')){
        backgroundColor = "#e9ecef"; //disabledの場合はグレー 
    }else{
        switch(selectedValue) {
            case "on":
                backgroundColor = "#e0ffff"; // lightcyan
                break;
            case "off":
                backgroundColor = "#FFFFFF"; // 白色
                break;
            case "auto":
                backgroundColor = "#ffffe0"; // lightyellow
                break;
            default:
                backgroundColor = "#FFFFFF"; // デフォルトの白色
            }    
    }
  
    e.style.backgroundColor = backgroundColor;
}

/////////////////////////////////////////
// Function
/////////////////////////////////////////

function resizeWindow():void{
    
    const windowheight:number = $(window).height() ?? 0; 
    const windowWidthWithAsobi:number = windowheight - 10; // 10pxは余裕を持たせる

}

let convIdCounter = 0;
function get_convId():number{
    convIdCounter += 1;
    return convIdCounter;
}

async function debateControl(query:string,apiType:string,searchflg:string) {
    console.log('debateControl');

    let prompttext:string = "";
    let displaytext:string = "";
    let htmltext:string = '<div class="clearfix li-option me-balloon"><div class="message-data smartphone-display"><img src="static/app/images/me.png" alt="avatar"></div><div class="message other-message-input smartphone-padding">@@displaytext@@</div></div>';

    if (apiType === "Debate"){
        switch (debate_stage) {
            // - 討論の手順\n\
            // 1. 主張Aの立論\n\
            case 1:
                displaytext = "1. 主張Aの立論";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = query;
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 2. 主張Bの反対尋問\n\
            case 2:
                displaytext = "2. 主張Bの反対尋問";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張B側からの主張A側に対する反対尋問を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 3. 主張Aの反対尋問に対する回答\n\
            case 3:
                displaytext = "3. 主張Aの反対尋問に対する回答";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張A側からの主張B側の反対尋問の回答を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 4. 主張Bの立論\n\
            case 4:
                displaytext = "4. 主張Bの立論";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張B側からの立論を行ってください。その際、上記を参考にしてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 5. 主張Aの反対尋問\n\
            case 5:
                displaytext = "5. 主張Aの反対尋問";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張A側からの主張B側の立論に対する反対尋問を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 6. 主張Bの反対尋問に対する回答\n\
            case 6:
                displaytext = "6. 主張Bの反対尋問に対する回答";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張B側からの主張A側の反対尋問の回答を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 7. 主張Bの反駁\n\
            case 7:
                displaytext = "7. 主張Bの反駁";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張B側からの反駁を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 8. 主張Aの反駁\n\
            case 8:
                displaytext = "8. 主張Aの反駁";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張A側からの反駁を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 9. 主張Bの最終弁論\n\
            case 9:
                displaytext = "9. 主張Bの最終弁論";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張B側からの最終弁論を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 10. 主張Aの最終弁論\n\
            case 10:
                displaytext = "10. 主張Aの最終弁論";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に主張A側からの最終弁論を上記を参考にして行ってください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            // 11. AIが下した勝敗とその理由\n\
            case 11:
                displaytext = "11. AIが下した勝敗とその理由";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "上記の主張Aと主張Bのディベートに勝敗をつけるとすれば、どちらが勝ちになりますか。その理由と共に答えてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信

                // 最後に、入力フィールドを表示する
                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide(); 

                break;
            default:
                break;
        }
        debate_stage += 1;
    }else if (apiType === "Meeting"){
        switch (debate_stage) {
            case 1:
                displaytext = "まずサービス企画部の部長からレビューし、ご意見を詳しく述べてください";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = query;
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            case 2:
                displaytext = "次にサービス営業部の部長から、ご意見を詳しく述べてください。";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に、サービス営業部の部長から、ご意見を詳しく述べてください。ご意見内容は、上記の検討内容を参考にし、サービス企画のレビューとしてご意見を述べてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            case 3:
                displaytext = "次にサービス開発部の部長から、ご意見を詳しく述べてください。";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に、サービス開発部の部長から、ご意見を詳しく述べてください。ご意見内容は、上記の検討内容を参考にし、サービス企画のレビューとしてご意見を述べてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            case 4:
                displaytext = "次にサービス運用部の部長から、ご意見を詳しく述べてください。";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "次に、サービス運用部の部長から、ご意見を詳しく述べてください。ご意見内容は、上記の検討内容を参考にし、サービス企画のレビューとしてご意見を述べてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            case 5:
                displaytext = "上記の参加者全員の意見を考慮した上でまとめの内容を述べてください。";
                $('#chatul').append(htmltext.replace(/@@displaytext@@/g, displaytext));
                prompttext = "上記の参加者全員の意見を考慮した上で次の内容を熟考し、詳しく述べてください。論述は文章だけではなく、箇条書きや表を使って文字で読む際にわかりやすく表現してください。\n\
\n\
‐ このサービス企画で他のサービスと比べて最も価値があり、差別化要素となると考えられる点を価値が高い順に述べてください。\n\
‐ このサービス企画で方針転換した方が良いと考えられる点を、重要度が高い順に述べてください。\n\
‐ このサービス企画の今後の課題を、重要度が高い順に述べてください。\n\
- このサービス企画の次アクション、重要度が高い順に述べてください。\n\
- このサービス企画の成功確率に点数をつけるとすると何点でしょうか？成功確率は0点が「世界で10人以下にしか普及しない」、50点が「世界で10000人程度に普及する」「100点が1000000人程度に普及する」で考えてください。";
                await postStreamingChatGptResponse(prompttext,get_convId(),apiType,searchflg); // ChatGPTに直接送信
                break;
            default:
                break;
        }
        debate_stage += 1;    
    }
}

function printDiv(divId: string) {
    let printContents = $("#"+ divId ).html();
    printContents = '<div id="chatui" class="col chat page-body-child"><div id="chatui-pp" class="chat-history smartphone-padding2 vetical-controll" style="height: auto !important;">'
    + printContents
    + '</div></div>';

    let iframe: HTMLIFrameElement = document.createElement('iframe');
    iframe.style.position = 'absolute';
    iframe.style.width = '0px';
    iframe.style.height = '0px';
    iframe.style.border = '0';
    document.body.appendChild(iframe);

    // iframeのドキュメントにコンテンツを書き込む
    // @ts-ignore
    let doc: Document = iframe.contentWindow.document;
    let htmlElement = doc.documentElement;
    // let htmlElement = doc.createElement('html');
    let headElement = doc.createElement('head');
    let titleElement = doc.createElement('title');
    let styleElement = doc.createElement('style');
    let bodyElement = doc.createElement('body');

    // Create and append link elements
    let linkElement1 = doc.createElement('link');
    linkElement1.href = "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css";
    linkElement1.rel = "stylesheet";
    linkElement1.type = "text/css";
    linkElement1.integrity = "sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC";
    linkElement1.crossOrigin = "anonymous";
    headElement.appendChild(linkElement1);

    linkElement1 = doc.createElement('link');
    linkElement1.href = "static/app/content/chatui.css";
    linkElement1.rel = "stylesheet";
    linkElement1.type = "text/css";
    headElement.appendChild(linkElement1);
    
    linkElement1 = doc.createElement('link');
    linkElement1.href = "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css";
    linkElement1.rel = "stylesheet";
    linkElement1.type = "text/css";
    headElement.appendChild(linkElement1);

    linkElement1 = doc.createElement('link');
    linkElement1.href = "static/app/content/github-markdown-light.css";
    linkElement1.rel = "stylesheet";
    linkElement1.type = "text/css";
    headElement.appendChild(linkElement1);

    linkElement1 = doc.createElement('link');
    linkElement1.href = "static/app/content/highlight.js/styles/github.css";
    linkElement1.rel = "stylesheet";
    linkElement1.type = "text/css";
    headElement.appendChild(linkElement1);

    titleElement.textContent = 'Print div';
    bodyElement.innerHTML += printContents;

    headElement.appendChild(titleElement);
    // @ts-ignore
    htmlElement.removeChild(htmlElement.firstChild);
    // @ts-ignore
    htmlElement.removeChild(htmlElement.firstChild);

    htmlElement.appendChild(headElement);
    htmlElement.appendChild(bodyElement);


    // 印刷が完了したらiframeを削除
    iframe.onload = function() {
        setTimeout(function() {
            // @ts-ignore
            //console.log(iframe.contentDocument.documentElement.innerHTML);
            // @ts-ignore
            iframe.contentWindow.focus();
            // @ts-ignore
            iframe.contentWindow.print();
            document.body.removeChild(iframe);
        }, 1000); // 500ミリ秒後に印刷を開始
    };
}

/////////////////////////////////////////
// Rest Service
/////////////////////////////////////////

// Jquery の triggerでイベンドハンドリングを行う
const serviceEvents = $({});
const baseurl = getBaseurl();

// SSEをグローバル変数として宣言
var sse;

// ChatGPTへの呼び出し
async function postStreamingChatGptResponse(query:string,convId:number,apiType:string,searchflg:string) {
    console.log('postStreamingChatGptResponse');

    if (now_session_id == 0){
        now_session_id = await getIdHttpResponse("session_id");
    }

    now_session_data.push({role: "user",content: query})

    let outhtmltext:string = "";
    let linetext:string = "";
    // let linehtmltext:string = "";
    let alltext:string = "";
    let firstflg:boolean = false;
    let whileTypingCharactor_temp:string = whileTypingCharactor;

    let apiUrl = "";
    let sendData = ""
    let searchtemp = "";
    let p_temp;

    switch (searchflg) {
        case 'on':
            searchtemp = "on";
            break;
        case 'auto':
            searchtemp = "auto";
            break;
        case 'off':
            searchtemp = "off";
            break;
        default:
            break;
    }

    switch (apiType) {
        case 'summary':
            apiUrl = "../summary";
            searchtemp = "off";
            p_temp = query;

            sendData = JSON.stringify({
                p: p_temp,
                search:searchtemp,
                sessionid:now_session_id,
                pageid:chatpage,
                });

            break;
        case 'search':
            apiUrl = "../documentsearch";
            p_temp = now_session_data;
            let select_option_list = $('#multiselect').val();

            sendData = JSON.stringify({
                p: p_temp,
                sessionid:now_session_id,
                pageid:chatpage,
                select_option_list,
                });
            break;
        case 'chatGPT':
        case 'Debate':
        case 'Meeting':
        case 'regularchat':
            apiUrl = "../chat";
            p_temp = now_session_data;

            sendData = JSON.stringify({
                p: p_temp,
                search:searchtemp,
                sessionid:now_session_id,
                pageid:chatpage,
                });
            break;
        default:
            break;
    }

    // - 討論の手順\n\
    // 1. 主張Aの立論\n\
    // 2. 主張Bの反対尋問\n\
    // 3. 主張Aの反対尋問に対する回答\n\
    // 4. 主張Bの立論\n\
    // 5. 主張Aの反対尋問\n\
    // 6. 主張Bの反対尋問に対する回答\n\
    // 7. 主張Bの反駁\n\
    // 8. 主張Aの反駁\n\
    // 9. 主張Bの最終弁論\n\
    // 10. 主張Aの最終弁論\n\
    let icon_image_path = "";
    if (apiType === "Debate"){
        switch (debate_stage) {
            case 1:
            case 3:
            case 5:
            case 8:
            case 10:
                icon_image_path = "static/app/images/b5.png";
                break;
            case 2:
            case 4:
            case 6:
            case 7:
            case 9:
                icon_image_path = "static/app/images/b6.png";
                break;
            default:
                icon_image_path = "static/app/images/ai.png";
                break;
        }
    }else if (apiType === "Meeting"){
        switch (debate_stage) {
            case 1:
                icon_image_path = "static/app/images/m9.png";
                break;
            case 2:
                icon_image_path = "static/app/images/f2.png";
                break;
            case 3:
                icon_image_path = "static/app/images/m3.png";
                break;
            case 4:
                icon_image_path = "static/app/images/f10.png";
                break;
            default:
                icon_image_path = "static/app/images/ai.png";
                break;
        }
    }else{
        icon_image_path = "static/app/images/ai.png";
    }

    // 回答の吹出しを用意
    var $myList = $('#chatul');
    $myList.append('<div id="outputdiv" class="clearfix li-option ai-balloon"><div class="message-data smartphone-display"><img id="pimg" src="' + icon_image_path +'" alt="avatar"></div><div class="message my-message markdown-body smartphone-padding" id="resmessege' + convId.toString() + '"></div></div>');

    $('#stop_button').show();

    // $('#resmessege'+ convId.toString()).html('<img src="static/app/images/typing-animation-3x.gif" width="42" height="28">');
    $('#resmessege'+ convId.toString()).html(whileTypingCharactor_temp);


    // @ts-ignore
    sse = new SSE( apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        payload: sendData
      });
    
    // Register event listeners.
    sse.addEventListener('open', function (e) {
        console.log('Connection opened.');
    });
    
    sse.addEventListener('error', function (e) {
        console.log('Connection error.');
        // alert('通信エラー: サーバーとの接続が切断されました。'+ e.data);
    });
    
    sse.addEventListener('abort', function (e) {
        console.log('Connection abort.');
        // sseの終了処理
        sse.close();
        alert('通信エラー: サーバーとの接続が切断されました。'+ e.data);

        now_session_data.push({role: "assistant",content: alltext})

        // @ts-ignore
        outhtmltext = marked.parse(alltext.trimEnd());

        whileTypingCharactor_temp = "";

        $('#inputtextarea').prop('disabled', false);
        $('#resmessege'+ convId.toString()).html(outhtmltext + linetext + whileTypingCharactor_temp);   

        $('#chat_button_spin').hide();
        // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
        $('#stop_button').hide();

    });
    
    sse.addEventListener('message', function (e) {
        // console.log('Received message:', e.data);

        let endflag = false;

        if (firstflg == false){

            $('#chat_button_spin').hide();
            // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
            $('#inputtextarea').css('height', "60px");
            $('#inputtextarea').val('');

            // 回答が開始したらScrollを1度だけ行う
            const scrollerInner = document.getElementById("chatui");
            if (scrollerInner !== null){
                scrollerInner.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"});
            }

            firstflg = true;
        };

        let tokendata = ""
        if(apiType === "summary"){
            tokendata = e.source.chunk;     
        }else{
            tokendata = e.data;
        }
        
        linetext = linetext + tokendata;
        linetext = linetext.replace(/@s@/g, " ");
        linetext = linetext.replace(/@n@/g, "\n");
        // console.log("linetext:" + linetext);

        if(linetext.includes("|E|")){
            endflag = true;
            linetext = linetext.replace("|E|", "");
        }
        
        if(linetext.includes("\n\n")){
            // let linetemp = ""; 
            // linetemp = linetext.replace(/@n@@n@/g, "\n\n");
            // linetext = linetemp.replace(/@n@/g, "\n");
            // console.log("linetext2:" + linetext);

            alltext = alltext + linetext;
            linetext = "";

            // @ts-ignore
            outhtmltext = marked.parse(alltext);
        }; 

        if(endflag == true){
            // linetext = linetext.replace(/@n@/g, "\n");
            alltext = alltext + linetext;
            linetext = "";
            // console.log("alltext:" + alltext.trimEnd());

            now_session_data.push({role: "assistant",content: alltext})
            // console.log(now_session_data)

            // @ts-ignore
            outhtmltext = marked.parse(alltext.trimEnd());
            // console.log(outhtmltext);

            // marked.jsのHTMLパースが脚注表現[^1^]に対応していないため置き変える。
            outhtmltext = outhtmltext.replace(/\[\^1\^\]/g, "<small>*1</small>");
            outhtmltext = outhtmltext.replace(/\[\^2\^\]/g, "<small>*2</small>");
            outhtmltext = outhtmltext.replace(/\[\^3\^\]/g, "<small>*3</small>");
            outhtmltext = outhtmltext.replace(/\[\^4\^\]/g, "<small>*4</small>");
            outhtmltext = outhtmltext.replace(/\[\^5\^\]/g, "<small>*5</small>");
            outhtmltext = outhtmltext.replace(/\[\^6\^\]/g, "<small>*6</small>");
            outhtmltext = outhtmltext.replace(/\[\^7\^\]/g, "<small>*7</small>");
            outhtmltext = outhtmltext.replace(/\[\^8\^\]/g, "<small>*8</small>");
            outhtmltext = outhtmltext.replace(/\[\^9\^\]/g, "<small>*9</small>");

            whileTypingCharactor_temp = "";


            // console.log("outhtmltext:" + outhtmltext);
            // console.log("alltext:" + alltext);

            //// mermaid start

            // mermaidのコードが含まれていた場合は図に変換する            
            let regex = /```mermaid([\s\S]*?)```/;
            let mermaidmatch = alltext.match(regex);
            
            if (mermaidmatch) {
                console.log("mermaid:" + mermaidmatch[1].trim());
                outhtmltext += '<div class="mermaid">\n' + mermaidmatch[1] + '</div>';

                // 1秒後にMermaidを実行
                setTimeout(function(){
                    console.log("mermaid exec");
                    // @ts-ignore
                    // Mermaidを初期化
                    mermaid.initialize({startOnLoad: true});

                    // @ts-ignore
                    // Mermaidのコードを解析して図を生成
                    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                    
                    // コードを折りたたみ可能にする
                    $('pre:has(code.language-mermaid)').wrap('<details></details>');
                    // $('code.language-mermaid').wrap('<details></details>');
                }, 1000);

            } else {
              console.log("Mermaid code is not match found.");
            }
            //// mermaid end

            // sseの終了処理
            sse.close();
            // DBの履歴に保存
            postHistoryHttpResponse()

            if(apiType === "Debate" && debate_stage <= 11){
                debateControl("",apiType,searchflg); // debateの次のステップを実施
            }else if(apiType === "Meeting" && debate_stage <= 5){
                debateControl("",apiType,searchflg); // debateの次のステップを実施
            }else{
                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();   
            }
        }
        $('#resmessege'+ convId.toString()).html(outhtmltext + linetext + whileTypingCharactor_temp);     

        
        // codeの色分けhighlight用
        // @ts-ignore
        hljs.highlightAll();

    });
    
    // Start the connection.
    sse.stream();

}

// SSEをグローバル変数として宣言
var sse2;
// ChatGPTへの呼び出し
async function postCodeInterpreterResponse(query:string,convId:number,apiType:string) {
    console.log('postCodeInterpreterResponse');

    if (now_session_id == 0){
        now_session_id = await getIdHttpResponse("session_id");
    }

    now_session_data.push({role: "user",content: query})

    let outhtmltext:string = "";
    let linetext:string = "";
    let alltext:string = "";
    let firstflg:boolean = false;
    let jsonflag:boolean = false;
    let jsontext:string = "";
    let whileTypingCharactor_temp:string = whileTypingCharactor;

    let apiUrl = "";
    let sendData = ""
    let p_temp;
    let Exec_lang = "";

    switch (apiType) {
        case 'CodeInterpreter':
        case 'CodeInterpreter_Preset':
            apiUrl = "../code_interpreter";
            Exec_lang = 'python';
            p_temp = now_session_data;

            sendData = JSON.stringify({
                p: p_temp,
                sessionid:now_session_id,
                pageid:chatpage,
                });
            break;
        case 'CodeInterpreter_Sql':
            apiUrl = "../code_interpreter_sql";
            Exec_lang = 'sql';
            p_temp = now_session_data;

            let schemaname_now = "";
            let tablename_now = "";
            // 現在開いているページのtable_nameを設定
            for (let k = 0; k < tableinfo_list.length; k++) {
                if (tableinfo_list[k].page_id === chatpage) {
                    schemaname_now = tableinfo_list[k].table_schema;
                    tablename_now = tableinfo_list[k].table_name;
                }
            }

            sendData = JSON.stringify({
                p: p_temp,
                sessionid:now_session_id,
                pageid:chatpage,
                schemaname:schemaname_now,
                tablename:tablename_now
                });
            break;
        default:
            break;
    }

    // 回答の吹出しを用意
    var $myList = $('#chatul');
    $myList.append('<div id="outputdiv" class="clearfix li-option ai-balloon"><div class="message-data smartphone-display"><img id="pimg" src="static/app/images/ai.png" alt="avatar"></div><div class="message my-message markdown-body smartphone-padding" id="resmessege' + convId.toString() + '"></div></div>');

    $('#stop_button').show();
    // $('#resmessege'+ convId.toString()).html('<img src="static/app/images/typing-animation-3x.gif" width="42" height="28">');
    $('#resmessege'+ convId.toString()).html(whileTypingCharactor);

    // @ts-ignore
    sse2 = new SSE( apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        payload: sendData
      });
    
    // Register event listeners.
    sse2.addEventListener('open', function (e) {
        console.log('Connection opened.');
    });

    sse2.addEventListener('readystatechange', function (e) {
        console.log('Connection readystatechange.');
    });

    sse2.addEventListener('error', function (e) {
        console.log('Connection error.');
    });
    
    sse2.addEventListener('abort', function (e) {
        console.log('Connection abort.');
        // sse2の終了処理
        sse2.close();
        alert('通信エラー: サーバーとの接続が切断されました。'+ e.data);

        // @ts-ignore
        outhtmltext = marked.parse(alltext.trimEnd());

        whileTypingCharactor_temp = "";

        $('#inputtextarea').prop('disabled', false);
        $('#resmessege'+ convId.toString()).html(outhtmltext + linetext + whileTypingCharactor_temp);   

        $('#chat_button_spin').hide();
        // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
        $('#stop_button').hide();


    });
    
    sse2.addEventListener('message', function (e) {
        //console.log('Received message:', e.data);

        let endflag = false;

        if (firstflg == false){

            $('#chat_button_spin').hide();
            // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
            $('#inputtextarea').css('height', "60px");
            $('#inputtextarea').val('');

            // 回答が開始したらScrollを1度だけ行う
            const scrollerInner = document.getElementById("chatui");
            if (scrollerInner !== null){
                scrollerInner.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"});
            }

            firstflg = true;
        };

        let tokendata = ""
        tokendata = e.data;
        
        linetext = linetext + tokendata;
        linetext = linetext.replace(/@s@/g, " ");
        linetext = linetext.replace(/@n@/g, "\n");
        linetext = linetext.replace(/@cs@/g, "<details><summary><span class='summary_inner'>"+ Exec_lang + "コードを見る<span class='summary_icon'></span></span></summary>\n\n```" + Exec_lang + "\n");
        linetext = linetext.replace(/@ce@/g, "\n```\n\n </details>");
        linetext = linetext.replace(/@ds@/g, "【処理内容】\n");
        linetext = linetext.replace(/@de@/g, "");
        linetext = linetext.replace(/@ps@/g, "<details><summary><span class='summary_inner'>プロンプトを見る<span class='summary_icon'></span></span></summary>\n\n```\n");
        linetext = linetext.replace(/@pe@/g, "\n```\n\n </details>");

        // console.log("linetext:" + linetext);

        if(linetext.includes("@js@")){
            jsonflag = true;
        }
        if(linetext.includes("@je@")){
            jsonflag = false;
            jsontext = jsontext + linetext;
            jsontext = jsontext.replace(/@js@/g, "");
            jsontext = jsontext.replace(/@je@/g, "");

            let jsondata = JSON.parse(jsontext) as type_res_CodeInterpreter;

            // @ts-ignore
            let output_markdown = marked.parse(jsondata.data);
            let markdowntext = output_markdown.replace(/<table>/g,'<table class="ci-table" style="overflow-x: auto; overflow-y: auto; max-height: 600px;">');
        
            if (jsondata.image_url !== ""){
                markdowntext += "\n\n![Image](" + jsondata.image_url + ")";
            }
            if (jsondata.data_url !== ""){
                markdowntext += "\n\nデータの[Download (Excelファイル)](" + jsondata.data_url + ')';
            }
            linetext = markdowntext;
        }

        // {から始まるデータはjsonなので、}が来るまで表示させずにまつ
        if(jsonflag == true){
            jsontext += linetext;

        }else{

            if(linetext.includes("|E|")){
                endflag = true;
                linetext = linetext.replace("|E|", "");
            }
            
            if(linetext.includes("\n\n")){

                alltext = alltext + linetext;
                linetext = "";

                // @ts-ignore
                outhtmltext = marked.parse(alltext);
            }; 

            if(endflag == true){
                // linetext = linetext.replace(/@n@/g, "\n");
                alltext = alltext + linetext;
                linetext = "";
                // console.log("alltext:" + alltext.trimEnd());

                now_session_data.push({role: "assistant",content: alltext})
                // console.log(now_session_data)

                // @ts-ignore
                outhtmltext = marked.parse(alltext.trimEnd());

                whileTypingCharactor_temp = "";

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();

                // console.log("alltext:" + alltext);

                // sse2の終了処理
                sse2.close();
                // DBの履歴に保存
                postHistoryHttpResponse()
            }

            $('#resmessege'+ convId.toString()).html(outhtmltext + linetext + whileTypingCharactor_temp);     
            
            // codeの色分けhighlight用
            // @ts-ignore
            hljs.highlightAll();
        }

    });
    
    // Start the connection.
    sse2.stream();

}

// 採番されたIdの取得
async function getIdHttpResponse(id_name:string):Promise<number> {

    let response = await fetch(baseurl + `getid?id_name=`+ id_name);
    let res = await response.json() as getIdModel;

    console.log('completeGetIdHttpResponse');
    console.log('session id:' + res.id);
    
    return Number(res.id);
}

// 登録されたドキュメント情報の取得
async function getlist_of_registered_document():Promise<Array<getlist_of_registered_documentModel>> {

    let response = await fetch(baseurl + `getlist_of_registered_document`);
    let res = await response.json() as Array<getlist_of_registered_documentModel>;

    console.log('completeGetlist_of_registered_documentHttpResponse');
    // console.log('session id:' + res);
    
    return res;
}

// 会話履歴の保存
async function postHistoryHttpResponse() {

    let sendData:string = JSON.stringify({
        p: now_session_data,
        sessionid:now_session_id,
        pageid:chatpage,
        });

    // RESTクライアントの実行
    $.post(baseurl + `conv_save2db`, sendData, function(res){
        if (res.statusCode == 200) {
            console.log(res.result);
        }else{
            console.log(res.statusCode);
        }
        console.log(res);
        }, "json");

}

// ファイルのアップロード
async function postPdfFileuploadHttpResponse(document_name:string, description:string, file:File|null,convId:number) {

    // 回答の吹出しを用意
    var $myList = $('#chatul');
    $myList.append('<div id="outputdiv" class="clearfix li-option ai-balloon"><div class="message-data smartphone-display"><img id="pimg" src="static/app/images/ai.png" alt="avatar"></div><div class="message my-message markdown-body smartphone-padding" id="resmessege' + convId.toString() + '"></div></div>');

    $('#stop_button').show();

    // $('#resmessege'+ convId.toString()).html('<img src="static/app/images/typing-animation-3x.gif" width="42" height="28">');
    $('#resmessege'+ convId.toString()).html(whileTypingCharactor);


    const headers = new Headers({
        // Content-Typeヘッダーは明示的に設定されていませんが、自動的に設定されます。
      })
    
      const body = new FormData()
      body.append("document_name", document_name)
      body.append("description", description)
      if (file != null) {
        body.append("file", file, file.name)
      }
    
      const data: RequestInit = {
        method: 'POST',
        headers: headers,
        body: body
      }
    
      const response = await fetch(baseurl + `document_upload_save`, data)
        .then((response) => {
          return (response.json()).then((data:type_res_document_upload_save) => { 
            
            if (data.status.includes("OK")) {
                console.log(data.status);
                let outmarkdowntext: string = "";
                let outhtmltext2: string = ""
                if (data.data.length != 0){
                    outmarkdowntext = "- 以下はPDFから抽出した目次です。目次が適切であると精度が向上します。想定した通りになっているか確認ください。\n- PDFは「Wordで開いて目次を編集し、PDFにエクスポートすること」で編集できます。\n|開始頁|終了頁|目次|\n| ---- | ---- | ---- |\n";
                    data.data.forEach(element => {
                        outmarkdowntext += "|"+ element.pageno_start.toString() + "|" + element.pageno_end.toString() +"|"+ element.chapter_title_all +"|\n";
                    });
                    // @ts-ignore
                    outhtmltext2 = marked.parse(outmarkdowntext.trimEnd());
                }
                // console.log(outmarkdowntext);

                $('#chat_button_spin').hide();
                // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
                $('#inputtextarea').css('height', "60px");
                $('#inputtextarea').val('');
    
                // 回答が開始したらScrollを1度だけ行う
                const scrollerInner = document.getElementById("chatui");
                if (scrollerInner !== null){
                    scrollerInner.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"});
                }

                // 回答の吹出しを用意
                $('#resmessege'+ convId.toString()).html("資料を熟読しました。この資料について別ページで要約や質問をしていいですよ。<br><br>" + outhtmltext2);  

                // codeの色分けhighlight用
                // @ts-ignore
                hljs.highlightAll();

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();

            }else{
                console.log(data.status);
                // alert('通信エラー: サーバーとの接続が切断されました。'+ data.status);
                // 回答の吹出しを用意
                $('#resmessege'+ convId.toString()).html(data.status);

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();

            }
            return data.status })
        }).catch((error) => {
            console.log(error)          
            alert('通信エラー: サーバーとの接続が切断されました。'+ error);
        })
    //   return response

}

// Sqlのテーブルのヘッダーを取得
async function postGetSqlTableHeadHttpResponse(convId:number) {
    // 回答の吹出しを用意
    var $myList = $('#chatul');
    $myList.append('<div id="outputdiv" class="clearfix li-option ai-balloon"><div class="message-data smartphone-display"><img id="pimg" src="static/app/images/ai.png" alt="avatar"></div><div class="message my-message markdown-body smartphone-padding" id="resmessege' + convId.toString() + '"></div></div>');

    $('#stop_button').show();

    // $('#resmessege'+ convId.toString()).html('<img src="static/app/images/typing-animation-3x.gif" width="42" height="28">');
    $('#resmessege'+ convId.toString()).html(whileTypingCharactor);

    console.log("now_session_id:" + now_session_id);
    if (now_session_id == 0){
        now_session_id = await getIdHttpResponse("session_id");
    }

    const headers = new Headers({
        // Content-Typeヘッダーは明示的に設定されていませんが、自動的に設定されます。
      })
    
    let schemaname_now = "";
    let tablename_now = "";
    // 現在開いているページのtable_nameを設定
    for (let k = 0; k < tableinfo_list.length; k++) {
        if (tableinfo_list[k].page_id === chatpage) {
            schemaname_now = tableinfo_list[k].table_schema;
            tablename_now = tableinfo_list[k].table_name;
        }
    }

    const data: RequestInit = {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            session_id: now_session_id.toString(),
            pageid: chatpage.toString(),
            schemaname: schemaname_now,
            tablename: tablename_now
        })
    }

    const response = await fetch(baseurl + `code_interpreter_sql_get_tablelayout`, data)
        .then((response) => {
          return (response.json()).then((data:type_res_sql_get_tablelayout) => { 
            
            if (data.status.includes("OK")) {

                $('#chat_button_spin').hide();
                $('#inputtextarea').css('height', "60px");
                $('#inputtextarea').val('');
    
                // 回答が開始したらScrollを1度だけ行う
                const scrollerInner = document.getElementById("chatui");
                if (scrollerInner !== null){
                    scrollerInner.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"});
                }
                // @ts-ignore
                let datarayout:string = marked.parse(data.datarayout.trimEnd());
                // @ts-ignore
                let data_describe:string = marked.parse(data.data_describe.trimEnd());
                datarayout = datarayout.replace('<table>','<table class="ci-table" style="overflow-x: auto; overflow-y: auto; max-height: 600px;">');
                // @ts-ignore
                let dateime_columns:string = marked.parse(data.dateime_columns.trimEnd());
                let outtexthtml:string = "データの読み込みができました。ご要望をどうぞ。<br/><br/>"
                + "<details><summary><span class='summary_inner'>先頭5行を見る<span class='summary_icon'></span></span></summary>"
                + "<div class='summary_content'>" + datarayout + "</div></details>"
                //  + "<details><summary><span class='summary_inner'>日時項目の期間を見る<span class='summary_icon'></span></span></summary>"
                //  + "<div class='summary_content'>" + dateime_columns + "</div></details>"
                 + "<details><summary><span class='summary_inner'>日付項目と数値項目の概略を見る<span class='summary_icon'></span></span></summary>"
                 + "<div class='summary_content'>" + data_describe + "</div></details>";

                // 回答の吹出しを用意
                $('#resmessege'+ convId.toString()).html(outtexthtml);  

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();

            }else{
                console.log(data.status);
                // alert('通信エラー: サーバーとの接続が切断されました。'+ data.status);
                // 回答の吹出しを用意
                $('#resmessege'+ convId.toString()).html(data.status);

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();
            }
            return data.status })
        }).catch((error) => {
          console.log(error)
          alert('通信エラー: サーバーとの接続が切断されました。'+ error);
        })
    //   return response

}

// ファイルのアップロード
async function postCsvFileuploadHttpResponse(file:File|null,presetfile:string,convId:number) {

    // 回答の吹出しを用意
    var $myList = $('#chatul');
    $myList.append('<div id="outputdiv" class="clearfix li-option ai-balloon"><div class="message-data smartphone-display"><img id="pimg" src="static/app/images/ai.png" alt="avatar"></div><div class="message my-message markdown-body smartphone-padding" id="resmessege' + convId.toString() + '"></div></div>');

    $('#stop_button').show();

    // $('#resmessege'+ convId.toString()).html('<img src="static/app/images/typing-animation-3x.gif" width="42" height="28">');
    $('#resmessege'+ convId.toString()).html(whileTypingCharactor);

    console.log("now_session_id:" + now_session_id);
    if (now_session_id == 0){
        now_session_id = await getIdHttpResponse("session_id");
    }

    const headers = new Headers({
        // Content-Typeヘッダーは明示的に設定されていませんが、自動的に設定されます。
      })
    
    const body = new FormData()
    body.append("session_id", now_session_id.toString())
    // presetfileがあれば、CSV名を送る
    if (presetfile != "") {
        body.append("presetfile", presetfile.toString())
    }
    // fileがあれば、fileを送る
    if (file != null) {
        body.append("file", file, file.name)
    }
    
    const data: RequestInit = {
        method: 'POST',
        headers: headers,
        body: body
    }
    
    const response = await fetch(baseurl + `code_interpreter_upload_csv`, data)
        .then((response) => {
          return (response.json()).then((data:type_res_csv_upload_save) => { 
            
            if (data.status.includes("OK")) {
                // console.log(data.status);
                // let outmarkdowntext: string = "";
                // let outhtmltext2: string = ""
                // if (data.data.length != 0){
                //     outmarkdowntext = "";
                //     // @ts-ignore
                //     outhtmltext2 = marked.parse(outmarkdowntext.trimEnd());
                // }

                $('#chat_button_spin').hide();
                // $('#chat_button').prop("disabled", false); # その画面で一度使ったら、もう使えないようにする
                $('#inputtextarea').css('height', "60px");
                $('#inputtextarea').val('');
    
                // 回答が開始したらScrollを1度だけ行う
                const scrollerInner = document.getElementById("chatui");
                if (scrollerInner !== null){
                    scrollerInner.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"});
                }
                // @ts-ignore
                let datarayout:string = marked.parse(data.datarayout.trimEnd());
                // @ts-ignore
                let data_describe:string = marked.parse(data.data_describe.trimEnd());
                datarayout = datarayout.replace('<table>','<table class="ci-table" style="overflow-x: auto; overflow-y: auto; max-height: 600px;">');
                // @ts-ignore
                let dateime_columns:string = marked.parse(data.dateime_columns.trimEnd());
                let outtexthtml:string = "データの読み込みができました。ご要望をどうぞ。<br/><br/>"
                + "<details><summary><span class='summary_inner'>先頭5行を見る<span class='summary_icon'></span></span></summary>"
                + "<div class='summary_content'>" + datarayout + "</div></details>"
                 + "<details><summary><span class='summary_inner'>日時項目の期間を見る<span class='summary_icon'></span></span></summary>"
                 + "<div class='summary_content'>" + dateime_columns + "</div></details>"
                 + "<details><summary><span class='summary_inner'>数値項目の概略を見る<span class='summary_icon'></span></span></summary>"
                 + "<div class='summary_content'>" + data_describe + "</div></details>";

                // 回答の吹出しを用意
                $('#resmessege'+ convId.toString()).html(outtexthtml);  

                // codeの色分けhighlight用
                // @ts-ignore
                // hljs.highlightAll();

                $('#inputtextarea').prop('disabled', false);
                $('#stop_button').hide();

            }else{
                console.log(data.status);
                alert('通信エラー: サーバーとの接続が切断されました。'+ data.status);

            }
            return data.status })
        }).catch((error) => {
          console.log(error)
          alert('通信エラー: サーバーとの接続が切断されました。'+ error);
        })
    //   return response

}


///////////////////////////////////////////
//// Data Models
///////////////////////////////////////////

type getIdModel = {
    id: number;
}

type session_data = {
    role: string;
    content: string;
}

type getlist_of_registered_documentModel = {
    document_filename: string;
    document_name: string;
    total_page_no: string;
    discription: string;
    document_url: string;
    create_timestamp: Date;
}

type type_res_document_upload_save = {
    status: string;
    data: Array<type_chapter_by_chapter>
}

type type_chapter_by_chapter = {
    pageno_start: number
    pageno_end: number    
    chapter_title_all: string
    leaf_flg: boolean
}

type type_res_csv_upload_save = {
    status: string;
    datarayout: string;
    data_describe:string;
    dateime_columns:string;
}

type type_res_sql_get_tablelayout = {
    status: string;
    datarayout: string;
    data_describe:string;
    dateime_columns:string;
}

type type_res_CodeInterpreter = {
    status: string;
    data: string;
    // process_description: string;
    image_url: string;
    data_url: string;
    // exec_code: string;
}

/////////////////////////////////////////
// Common Tools
/////////////////////////////////////////

// BaseURL取得
function getBaseurl():string {
    return location.protocol + "//" + location.host + "/";
}
