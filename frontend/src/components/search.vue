<template>

  <div class="Search">
    <label>请选择表格:</label>
    <select v-model="selected" class="Select">
        <option disabled value="">选择表格</option>
        <option v-for="option in options" v-bind:value="option.value" class="options">
            {{ option.text }}
        </option>
    </select>
    <label v-show="retItems.length">该表格对应的自然语言问题:</label>
    <select v-model="selectedNL" class="SelectNL" v-show="retItems.length">
        <option disabled value="">请选择自然语言问题</option>
        <option v-for="question in questionListShow" v-bind:value="question.value" class="options">
            {{ question.text }}
        </option>
    </select>
    <button class="button" v-show="retItems.length" v-on:click="convert" v-bind:disabled="selectedNL === ''">CONVERT</button>

    <h2 v-show="errorinfo">暂无数据，请重新输入</h2>
    <div class="container left" v-show="retItems.length">
        <table>
            <thead>
            <tr>
                <th v-for="title in titles">{{ title }}</th>
            </tr>
            </thead>
            <tbody>
                <tr v-for="(item, i) in retItems" v-show="i < selectedP * limit">
                    <template v-if="i >= (selectedP - 1) * limit">
                    <td v-for="value in item">
                        {{ value }}
                    </td>
                    </template>
                </tr>
            </tbody>
        </table>

        <div v-show="datacnts>10" class="pageselect">
            <select class="showpages" @change="changepages" v-model="selectedP">
                <option v-for="opt in pageoptions" v-bind:value="opt.value" class="options">
                    {{ opt.text }}
                </option>
            </select>
            <p>每页显示数据条数：
                <input 
                    type="int"
                    class="limitInput" 
                    v-model="limit"
                    v-on:keyup.enter="changepages"
                />
            </p>
        </div>
        <p v-model="datacnts">表格‘{{ selected }}’中有 {{ datacnts }} 条数据</p>
    </div>
     <div class="container right" v-show="retItems.length">
        <div class="right-left">
            <label>预测的sql语句：</label><br/>
            <textarea class="textarea" cols='39' rows='4'>{{ sql_pred }}</textarea>
        </div>
        <br>
        <div class="right-right">
            <label>正确的sql语句：</label><br/>
            <textarea class="textarea" cols='39' rows='4'>{{ sql_gt }}</textarea>
        </div>
        
        <br><br>
        <button class="button" v-bind:disabled="queryDisabled" v-on:click="query" >QUERY</button>

        <br><br>

        <table style="width:auto">
            <thead>
            <tr>
                <th>result</th>
            </tr>
            </thead>
            <tbody>
                <tr>
                    <td>
                        {{ result }}
                    </td>
                </tr>
            </tbody>
        </table>

        <p v-model="resultcnts">查询结果有 {{ resultcnts }} 条数据</p>
    </div>
  </div>
</template>

<script>

// 改为CDN引入
// import axios from 'axios'
export default {
  name: 'Search',
  data () {
    return {
      limit : 10,
      selected: '',
      selectedNL: '',
      selectedP: 1,
      searchStr: '',
      pageStr: '',
      errorinfo: '',
      datacnts: 0,
      pageoptions: [],
      options: [
      ],
      retItems: [],
      analysisInfos: [],
      tableNames: [],
      questionList: [],
      questionListShow: [],
      sqlGt: [],
      sqlPred: [],
      titles: [],
      sql_gt: '',
      sql_pred: '',
      queryDisabled: true,
      result: '',
      resultcnts: 0,
    }
  },
  mounted: function() {
    axios.get('/get_table_names')
        .then(response => {
            this.tableNames = response.data

            for (let tableIdx in this.tableNames ) {
                this.options.push({
                    text: this.tableNames[tableIdx],
                    value: this.tableNames[tableIdx]
                });
            }
        })
        .catch(error => {
            console.log(error);
        });
    axios.get('/get_data')
        .then(response => {
            let questionList = response.data['question_list']
            for(let idx in questionList){
                this.questionList.push({
                    text: questionList[idx],
                    value: idx
                })
            }
            this.sqlGt = response.data['sql_gt']
            this.sqlPred = response.data['sql_pred']
        })
        .catch(error => {
            console.log(error);
        });
  },
  watch: {
      selected: function(val){
        this.selectedNL = ''
        this.sql_gt = ''
        this.sql_pred = ''
        this.queryDisabled = true
        this.pageoptions = []
        this.selectedP = 1
        let data = {'val': val}
        axios.post('/get_table', data)
            .then(response => {
                
                let res = eval(response.data)
                this.titles = []
                for (let key in res[0])
                    this.titles.push(key)

                this.retItems = res;

                this.datacnts = res.length;
                var n = 0;
                while ( n < Math.ceil(this.datacnts/this.limit)) {
                    n = n + 1;
                    this.pageoptions.push({
                        text: '第 ' +  n + ' 页',
                        value: n
                    });
                }

                this.questionListShow = []
                for(let idx in this.questionList){
                    let question = this.questionList[idx]
                    if(this.sqlGt[idx].indexOf(val) != -1){
                        this.questionListShow.push(question)
                    }
                }
            })
            .catch(error => {
                console.log(error);
            });
      },
      selectedNL: function(val){
        this.sql_gt = ''
        this.sql_pred = ''
        this.queryDisabled = true
      },
  },
  methods:{
        convert: function() {
            let idx = this.selectedNL
            this.sql_pred = this.generateLines(this.sqlPred[idx])
            this.sql_gt = this.generateLines(this.sqlGt[idx])
            this.queryDisabled = false
        },
        query: function() {
            let data = {'query': this.sqlPred[this.selectedNL]}
            axios.post('/query_db', data)
            .then(response => {
                let res = eval(response.data)

                if(JSON.stringify(res) == "[]"){
                    this.result = '查询出错，没有结果'
                    this.resultcnts = 0
                }
                else{
                    this.result = res[0]['result']
                    this.resultcnts = res.length
                }
                
            })
            .catch(error => {
                console.log(error);
            });
        },
        search: function () {
        },
        generateLines: function(text) {
            let content = text
            let from_idx = content.indexOf('FROM')
            let where_idx = content.indexOf('WHERE')
            content = content.slice(0, from_idx) + '\n' + content.slice(from_idx, where_idx) + '\n' + content.slice(where_idx)
            return content
        },
        changepages: function() {
        }
    }
}
</script>

<style>
@import url(http://www.bootcss.com/p/buttons/css/buttons.css);
h1, h2 {
  font-weight: normal;
}

h1 {
  color: #fff;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

table{
    margin: auto;
    border:1px solid none;
    padding: 20px;
    border-collapse: collapse;
    font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    font-size: 0.8em;
} 

.Search {

}

.container {
  text-align: center;
  overflow: hidden;
  width: 40em;

  margin: 20px;
}

.left {
  position: absolute;
  width: 60%;
}

.right {
  margin-left: 60%;
  width: 30%;
  height: 35em;
}



.container table {
  width: 80%;

}

.container td {
  font-size: 3px;
}
.container td, .container th {
  font-size: 1.2em;
  overflow: auto;
  padding: 5px;
  border-bottom: 1px dashed #dbb;
}

.container th {
  border-bottom: 1px solid #ddd;
  position: relative;
  width: 30px;
}

.button {
    margin: 0 0 0 10px;
    height: 40px;
    color: black;
    border-radius: 10px;
    background-color: white;
}

.button .p {
   	font-family: 'Roboto'; 
	text-align: center;
  	text-transform: uppercase;
    color: #FFF;
    user-select: none;
}
.button:disabled {
    background: grey;
}

.searchInput {
    outline: none;
    height: 30px;
    width: 480px;
    border : 1px solid  #FFFFFF;
    padding : 15px 30px 15px 30px;
    font-size: 1em;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
}
.searchInput:focus {
    box-shadow: 2px 2px 2px #336633;
}
.limitInput {
    outline: none;
    height: 15px;
    width: 20px;
    border : 1px solid  #FFFFFF;
    padding : 5px 5px 5px 5px;
    font-size: 1em;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
}
.limitInput:focus {
    box-shadow: 2px 2px 2px #336633;
}
.Select {
    border : 1px solid  #FFFFFF;
    font-size: 1em;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    outline: none;
    border: none;
    margin: 10px;
    padding: 0 0 0 10px;
}
.Select .options {
    outline: none;
    border: none;
    width: 300px;
}
.Select {
    height: 62px;
    width: 300px;
}
.SelectNL {
    border : 1px solid  #FFFFFF;
    font-size: 1em;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    outline: none;
    border: none;
    padding: 0 0 0 10px;
    margin: 0 0 0 20px;
}
.SelectNL .options {
    outline: none;
    border: none;
}
.SelectNL {
    height: 62px;
    width: 700px;
}
.textarea {
    height: 100px;
    border : 1px solid  #FFFFFF;
    font-size: 1em;
    font-weight: bold;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    outline: none;
    border: none;
    padding: 10px;
    margin: 10px 0 0 0;
}
.showpages {
    border : 1px solid  #FFFFFF;
    font-size: 1em;
    font-family: BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    outline: none;
    border: none;
    padding: 0 0 0 10px;
    position: relative;
    margin: 0 auto;
    margin-top: 1em;
}
.pageselect input{
}
</style>
