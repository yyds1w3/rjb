from langchain_core.prompts import ChatMessagePromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate
# 角色:Assitant, user system(AI的身份) 
# 一句话提示词
prompt_template = PromptTemplate.from_template(

)
# 聊天消息提示词
chat_template = ChatMessagePromptTemplate.from_messages(
    [
        {},
        {}
    ]
)
result = xxx_template.format()
print(result)
'''
chat_template = ChatMessagePromptTemplate.from_messages(
    [
        SystemMessage(
            content=(

            )
        ),
        HumanMessagePromptTemplate.from_template("{text}")    
    ]
)
'''

# 上下文提示词感觉没用

# 举例子
examples = [
    {},
    {}
]
exampl_prompt = PromptTemplate(input_variables=["question","answer"], 
template = "问题 : {quesition}\\n{answer}")
prompt = FewShotPromptTemplate(
    
)