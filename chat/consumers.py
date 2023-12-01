import json
import os
from datetime import timedelta, datetime
# from . utilities import when_withdraw,transaction_status,can_not_withdraw
from .gpt_functions.cant_withdraw.can_not_withdraw import can_not_withdraw
from .gpt_functions.when_withdraw.when_withdraw import when_withdraw
from .gpt_functions.transaction_status.transaction_status import transaction_status
from .gpt_functions.how_much_salary.how_much_salary import how_much_salary
from .gpt_functions.zero_balance.zero_balance import zero_balance
from .gpt_functions.admin_fees.admin_fees import admin_fees
from .gpt_functions import constants
import openai
import pinecone
from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import connection
from langchain.callbacks.streaming_stdout_final_only import (
    FinalStreamingStdOutCallbackHandler,
)
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.vectorstores import Pinecone

from .models import Message

openai.api_key = os.environ.get("OPENAI_API_KEY")
env_name = os.environ.get("ENV_NAME")
print(env_name)
# ---------------------------
embeddings = OpenAIEmbeddings()

pinecone.init(
    api_key=os.environ.get("PINECONE_API_KEY"),  # find at app.pinecone.io
    environment=os.environ.get("PINECONE_ENV"),  # next to api key in console
)
index_name = os.environ.get("PINECONE_INDEX_NAME")

whatsapp_chat_support_url="https://api.whatsapp.com/send/?phone=6281315276948"
function_descriptions = constants.function_descriptions

# -------------------------
#
# def convert_to_openai(messages):
# -------------

# ----------

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        if "memory" not in self.scope["session"]:
            self.scope["session"]["memory"] = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )
        # memory = ConversationBufferMemory()
        # Access the conversation buffer memory for this session
        self.memory = self.scope["session"]["memory"]
        # username will always same as room_name
        prev_messages = await self.fetch_messages(self.room_name, self.room_name)
        for msg in prev_messages:
            self.memory.chat_memory.add_user_message(msg["content"])

    async def disconnect(self, event):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        raise StopConsumer()
    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data["message"]
        username = data["username"]
        room = data["room"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": user_message,
                "username": username,
            },
        )
        labels = await self.fetch_label(self.room_name, username)
        for label in labels:
            print("****")
            print(label)
        prev_messages = await self.fetch_messages2(self.room_name)
        # for mes in prev_messages:
        #     print(mes)

        ai_message = await self.normal_gpt(user_message, prev_messages, self.room_name, room, username)

        # username will always same as room_name
        # reset memory object for each event then fetch new messages from DB
        self.memory.clear()
        prev_messages_qna = await self.fetch_messages(self.room_name, self.room_name)
        for msg in prev_messages_qna:
            self.memory.chat_memory.add_user_message(msg["content"])

        print(ai_message)
        if (ai_message == "Manager"):

            ai_message = await self.qna(user_message, self.memory)

            if ai_message.find('whatsapp')!=-1 or ai_message.find('wa.me')!=-1:
                humanRequired = True
            else:
                humanRequired = False
            await self.save_message(username, room, user_message,'FAQ',humanRequired)
            await self.save_message("Ai", room, ai_message, 'FAQ',humanRequired)
            labels = await self.fetch_label(self.room_name,username)
            for label in labels:
                print("****")
                print(label)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "username": "Ai",
                "message": ai_message,
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                }
            )
        )

    @staticmethod
    @sync_to_async
    def save_message(username, room, message, label,humanRequired):
        Message.objects.create(username=username, room=room, content=message, label =label, humanRequired=humanRequired)

    @staticmethod
    @sync_to_async
    def fetch_messages(room_name, username):
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        messages = list(
            Message.objects.filter(room=room_name, username=username, date_added__gte=twenty_four_hours_ago)
            .order_by("-id")[:5]
            .values("content")
        )
        if not messages:
            return []
        # for i in messages:
        #     print(i)
        return list(messages)

    @staticmethod
    @sync_to_async
    def fetch_messages2(room_name):
        messages = (Message.objects.filter(room=room_name)
                    .order_by("-id")[:3]
                    .values("content"))
        if not messages:
            return []
        # for i in messages:
        #     print(i)

        return list(messages)
    @staticmethod
    @sync_to_async()
    def fetch_label(room_name,username):
        labels = (Message.objects.filter(room=room_name, username=username).order_by("-id")[:3].values("label","humanRequired"))
        return list(labels)



    @staticmethod
    async def normal_gpt(message, memory, room_name, room, username):
        '''
        Hi, you are an assistant for queries to an account manager; you are talking to a customer and have the history
        of conversation just for reference but always consider most recent one or ask user to enter again if confused.
        You need to decide if you can handle the customer query or your manager needs to handle the query.
        If the manager needs to handle the query your reply should only be “Manager”.
        '''

        global function_response
        init_prompt = constants.init_prompt
        user_message = message

        prompt_suffix = constants.prompt_suffix
        label = ''
        messages = [{"role": "system", "content": init_prompt}]
        # for mes in memory:
        #     messages.append({"role": "user", "content": mes['content']})
        # messages.extend(memory)
        messages.append({"role": "user", "content": message+prompt_suffix})
        for mes in messages:
            print(mes)
        completion = openai.ChatCompletion.create(
            model='gpt-4',
            messages=messages,
            # max_tokens=1000,
            functions= function_descriptions,
            function_call="auto",
        )

        message = completion["choices"][0]['message']['content']
        print("--------------", message, "------------------")
        is_func_invoked = completion["choices"][0]['message'].get("function_call")
        if (is_func_invoked == None and message):
            return message
        else:
            function_call = False
            function_name = completion["choices"][0]['message']["function_call"]["name"]
            if function_name == "can_not_withdraw":
                print("can_not_withdraw called")
                label ="Pre-Transaction"
                function_response = await can_not_withdraw(room_name)
                if (env_name=="staging"):
                    function_response = f"Function Name: **--- {function_name} ---**  \n\n Result: {function_response}"
                function_call = True
            elif function_name=="how_much_salary":
                print("how_much_salary called")
                label ="Salary and limit balance"
                function_response = await how_much_salary(room_name)
                if (env_name=="staging"):
                    function_response = f"Function Name: **--- {function_name} ---** \n\n Result: {function_response}"
                function_call = True
            elif function_name == "when_withdraw":
                print("when_Withdraw called")
                label ="Withdrawal cycle"
                function_response = await when_withdraw(room_name)
                if (env_name=="staging"):
                    function_response = f"Function Name: **--- {function_name} ---** \n\n Result: {function_response}"
                function_call = True
            elif function_name == "zero_balance":
                print("zero_balance called")
                label ="Zero balance"
                function_response = await zero_balance(room_name)
                if (env_name == "staging"):
                    function_response = f"Function Name: **--- {function_name} ---** \n\n Result: {function_response}"
                function_call = True
            elif function_name == "admin_fees":
                print("admin_fees called")
                label =f"{function_name}"
                function_response = await admin_fees(room_name)
                if (env_name=="staging"):
                    function_response = f"Function Name: **--- {function_name} ---** \n\n Result: {function_response}"
                function_call = True
            elif function_name == "transaction_status":
                print("transaction_status called")
                label ="Post-Transaction"
                print(label)
                function_response = await transaction_status(room_name)
                if (env_name=="staging"):
                    function_response = f"Function Name: **--- {function_name} ---** \n\n Result: {function_response}"
                function_call = True
            if function_call:
                if function_response != "Manager":
                    humanRequired = False
                    if function_response.find('whatsapp')!=-1:
                        humanRequired = True
                        await ChatConsumer.save_message(username, room, user_message, label, humanRequired)
                        await ChatConsumer.save_message('Ai', room, function_response, label, humanRequired )
                    else:
                        await ChatConsumer.save_message(username, room, user_message, label, humanRequired)
                        await ChatConsumer.save_message('Ai', room, function_response, label, humanRequired)
                return function_response
            else:
                return "Error Code Func-001"

    @staticmethod
    async def qna(message, memory):

        prefix = str(os.environ.get("PREFIX"))
        suffix = str(os.environ.get("SUFFIX"))
        docsearch = Pinecone.from_existing_index(index_name, embeddings)

        llm = ChatOpenAI(
            # openai_api_key="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",
            model_name="gpt-3.5-turbo",
            # model_name="gpt-4",
            temperature=0.0,
            callbacks=[FinalStreamingStdOutCallbackHandler()],
        )
        messages = [
            SystemMessagePromptTemplate.from_template(prefix),
            HumanMessagePromptTemplate.from_template(suffix),
        ]

        PROMPT = ChatPromptTemplate.from_messages(messages)
        combine_docs_chain_kwargs = {"prompt": PROMPT}

        qa = ConversationalRetrievalChain.from_llm(
            llm=llm,
            chain_type="stuff",
            combine_docs_chain_kwargs=combine_docs_chain_kwargs,
            retriever=docsearch.as_retriever(),
            verbose=True,
            memory=memory,
        )

        # res = agent_chain.run({'input':message})
        print(qa)
        input_dict = {"question": message}
        res = qa.run(input_dict)
        print("-------")
        print(res)
        return res

    # @staticmethod
    # @sync_to_async
    # def can_not_withdraw(emp_id):
    #     with connection.cursor() as cursor:
    #             # Check if not within open cycle
    #         cursor.execute(f'select "isLockPeriod" from gg_daily_balance where "employeeId" = {emp_id} order by "createdAt" DESC LIMIT 1;')
    #         is_lock_period = cursor.fetchone()
    #
    #         if is_lock_period and is_lock_period[0] == True:
    #             lock_period_status = "Employee is not in open cycle."
    #             return "You are currently outside the salary withdrawal period. You can withdraw your salary between {start_date} and {end_date}."
    #         elif is_lock_period and is_lock_period[0] == False:
    #             lock_period_status = "Employee is in open cycle."
    #
    #             # Check if employer is suspended
    #         cursor.execute(
    #                 f'select status from gg_employer where status != \'active\' and id = (select "employerId" from gg_employee where id = {emp_id} )')
    #         employer_status = cursor.fetchone()
    #
    #         if employer_status:
    #             employer_status = "Employer is suspended."
    #             return "Currently, your company is unable to perform transactions. Please contact your HR department to resume transactions."
    #         else:
    #             employer_status = "Employer is not suspended."
    #
    #             # Check if employee is suspended
    #         cursor.execute(f'select status from gg_employee where status != \'active\' and id = {emp_id}')
    #         employee_status = cursor.fetchone()
    #
    #         if employee_status:
    #             employee_status = "Employee is suspended."
    #             return "At the moment, you are not allowed to perform transactions. Please contact your HR department for further clarification."
    #         else:
    #             employee_status = "Employee is not suspended."
    #     return f"It appears that there is an issue with the system. Please contact our expert team to assist you {whatsapp_chat_support_url}."
    #
    # @staticmethod
    # @sync_to_async
    # def when_withdraw(emp_id):
    #     with connection.cursor() as cursor:
    #         cursor.execute(f"""
    #             SELECT gg_payment_cycle."firstWorkingDate"::DATE,
    #                    gg_payment_cycle."endWorkingDate"::DATE,
    #                    gg_salary_profile."numberOfLockPeriod",
    #                    gg_salary_profile."withdrawalLockType"
    #             FROM gg_payment_cycle
    #             JOIN gg_salary_profile
    #             ON gg_payment_cycle."salaryProfileId" = gg_salary_profile.id
    #             WHERE gg_payment_cycle."employeeId" = {emp_id}
    #             ORDER BY gg_payment_cycle."createdAt" DESC
    #             LIMIT 1;
    #         """)
    #         results = cursor.fetchone()
    #
    #     if results:
    #         first_working_date, end_working_date, number_of_lock_period, withdrawal_lock_type = results
    #         if withdrawal_lock_type == 'FLEXIBLE':
    #             start_date = first_working_date
    #             end_date = end_working_date - timedelta(days=number_of_lock_period)
    #         elif withdrawal_lock_type == 'FIXED':
    #             start_date = first_working_date
    #             end_date = datetime(end_working_date.year, end_working_date.month, number_of_lock_period)
    #         else:
    #             start_date = None
    #             end_date = None
    #     if start_date and end_date:
    #         return f'''Based on latest information from your HR, your salary can be accesed between {start_date} until {end_date} this cycle. Outside of those time range, you can not withdraw money. Please reach out to your HR department if you have further question about cycle date changes.'''
    #
    #     return "Please reach out to your HR department if you have further question about cycle date changes."
    #
    #
    # @staticmethod
    # @sync_to_async
    # def transaction_status(emp_id):
    #     with connection.cursor() as cursor:
    #         # Check if transaction time is under 15 minutes ago
    #         cursor.execute(
    #             f'select "createdAt" from gg_transaction where "employeeId" = {emp_id} order by "createdAt" DESC limit 1;')
    #         transaction_time = cursor.fetchone()
    #
    #         if transaction_time and (datetime.now() - transaction_time[0]).total_seconds() < 900:
    #             transaction_status = "The transaction is still being processed. Please wait for 15 minutes and check if the transaction is still pending."
    #             return transaction_status
    #         else:
    #             transaction_status = None
    #
    #         # Get distinct unsuccessful transaction IDs
    #         cursor.execute(
    #             f'select id from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\') order by "createdAt" DESC;')
    #         transaction_ids = cursor.fetchall()
    #
    #         if transaction_ids:
    #             transaction_ids = ', '.join([str(id[0]) for id in transaction_ids])
    #             transaction_ids_status = f"We found {len(transaction_ids)} transactions that are not successful with the followingtransaction IDs: {transaction_ids}. Please reach our customer support using {whatsapp_chat_support_url}"
    #             return transaction_ids_status
    #         else:
    #             transaction_ids_status = None
    #
    #         # Check if no transaction found
    #         cursor.execute(f'select count(id) from gg_transaction where "employeeId" = {emp_id} and "transStatus" not in (\'COMPLETED\') order by "createdAt" DESC;')
    #         transaction_count = cursor.fetchone()
    #
    #         if transaction_count and transaction_count[0] == 0:
    #             no_transaction_status = f"We did not found any pending transaction. Please reach out to our expert team with the WhatsApp URL below {whatsapp_chat_support_url}"
    #             return no_transaction_status
    #         else:
    #             no_transaction_status = None
    #
    #     return  f"We did not found any pending transaction. Please reach out to our expert team with the WhatsApp URL below {whatsapp_chat_support_url}"
    #
