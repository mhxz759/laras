from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, Application
import logging

# Configurações do bot
API_TOKEN = '7615282326:AAE3yBoDlG_rMEGZCwq0NtZ0jivGwu1WmXU'
ADMIN_ID = 6776809071
PIX_KEY = "00020101021126580014br.gov.bcb.pix01363fc27349-d9af-4043-a8f9-b8861b182f655204000053039865802BR5922FERNANDO H DA S FREIRE6013RIBEIRAO DAS 62070503***630424E6"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulando banco de dados
user_balances = {}  # Exemplo: {user_id: saldo}
pending_recharges = {}  # Exemplo: {user_id: valor_recarregar}
logins = []  # Exemplo: [{'nome': ..., 'valor': ..., 'email': ..., 'senha': ..., 'duracao': ...}]

# Função de início
async def start(update: Update, context):
    user_id = update.message.from_user.id
    user_balances[user_id] = user_balances.get(user_id, 0)  # Inicializa saldo como 0

    keyboard = [
        [InlineKeyboardButton("💰 Recarregar Saldo", callback_data='recharge')],
        [InlineKeyboardButton("🛒 Ver Laras Disponíveis", callback_data='list_logins')]  # Nome alterado aqui
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏦 𝗕𝗲𝗺-𝘃𝗶𝗻𝗱𝗼 𝗮 𝗺𝗲𝗹𝗵𝗼𝗿 𝗹𝗼𝗷𝗮 𝗱𝗼 𝘁𝗲𝗹𝗲𝗴𝗿𝗮𝗺 𝗰𝗼𝗺 𝗶𝗻𝘁𝘂𝗶𝘁𝗼 𝗱𝗲 𝗺𝗲𝗹𝗵𝗼𝗿𝗮𝗿 𝗰𝗮𝗱𝗮 𝘃𝗲𝘇 𝗺𝗮𝗶𝘀 𝗮 𝗲𝘅𝗽𝗲𝗿𝗶𝗲𝗻𝗰𝗶𝗮 𝗱𝗼 𝗰𝗹𝗶𝗲𝗻𝘁𝗲 ✨\n\n"
        "➤ Todas Laras Validadas\n"
        "➤ Caso tenha poblemas contate suporte @Snow4055\n"
        "➤ Boas Compras\n\n"
        "👤 Seu perfil\n"
        f" ├🪪 ID: {user_id}\n"
        f" ├💸 Saldo: R$ {user_balances.get(user_id, 0):.2f}\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=reply_markup
    )

# Função de recarga
async def recharge(update: Update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    pending_recharges[user_id] = 0  # Inicia o estado de pendência para recarga
    await query.message.reply_text(
        "Digite o valor que deseja recarregar (em R$).\n"
        f"Use a chave Pix abaixo para realizar o pagamento:\n\n"
        f"🔑 **Chave Pix:**\n{PIX_KEY}\n\n"
        "Após realizar o pagamento, aguarde a confirmação do administrador."
    )

# Processar o valor digitado para recarga
async def process_recharge_value(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in pending_recharges:
        await update.message.reply_text("Use o botão de recarga antes de digitar o valor.")
        return

    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Digite um valor maior que zero.")
            return

        pending_recharges[user_id] = amount
        await update.message.reply_text(
            f"🚀 Solicitação de recarga criada!\n"
            f"Valor: R$ {amount:.2f}\n\n"
            f"🔑 **Chave Pix:**\n{PIX_KEY}\n\n"
            "Aguarde o administrador confirmar o pagamento."
        )

        # Notifica o administrador
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 Nova solicitação de recarga! 🚨\n\n"
                 f"Usuário: {user_id}\n"
                 f"Valor: R$ {amount:.2f}\n\n"
                 f"Use o comando /confirmar <user_id> <valor> para confirmar."
        )

    except ValueError:
        await update.message.reply_text("Digite um valor válido em R$.")

# Exibir Laras disponíveis
async def list_logins(update: Update, context):
    query = update.callback_query
    await query.answer()

    if not logins:
        await query.message.reply_text("Ainda não há Laras disponíveis para compra.")
        return

    keyboard = []
    for login in logins:
        button_text = f"{login['nome']} - R$ {login['valor']:.2f}"
        callback_data = f"buy_{login['nome']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Escolha a Lara que deseja comprar:", reply_markup=reply_markup)

# Processar compra
async def process_purchase(update: Update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_login = query.data.split("_")[1]  # Obtém o nome do login

    # Procura o login no "banco de dados"
    login = next((l for l in logins if l['nome'] == selected_login), None)
    if not login:
        await query.message.reply_text("Lara não encontrada.")
        return

    # Verifica saldo
    user_balance = user_balances.get(user_id, 0)
    if user_balance < login['valor']:
        await query.message.reply_text(
            "❌ Você não possui saldo suficiente para comprar esta lara.\n"
            "Recarregue seu saldo e tente novamente."
        )
        return

    # Realiza a compra
    user_balances[user_id] -= login['valor']
    logins.remove(login)  # Remove a lara da lista após a compra

    await query.message.reply_text(
        f"✅ Compra efetuada com sucesso!\n\n"
        f"💲 SALDO ATUAL: R$ {user_balances[user_id]:.2f}\n"
        f"💰 VALOR PAGO: R$ {login['valor']:.2f}\n"
        f"⏰ VALIDADE: {login['duracao']}\n"
        f"📅 COMPRA: {login['nome']}\n\n"
        f"🔐 **DADOS DE ACESSO:**\n"
        f"📧 EMAIL: {login['email']}\n"
        f"🔑 SENHA: {login['senha']}"
    )

# Comando para adicionar Laras
async def adicionar(update: Update, context):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return

    try:
        login_data = ' '.join(context.args)
        if not login_data:
            await update.message.reply_text("Por favor, forneça os dados no formato: NOME/VALOR/EMAIL/SENHA/DURAÇÃO.")
            return

        parts = login_data.split('/')
        if len(parts) != 5:
            await update.message.reply_text("Formato inválido! Use: NOME/VALOR/EMAIL/SENHA/DURAÇÃO.")
            return

        nome, valor, email, senha, duracao = parts
        logins.append({
            'nome': nome,
            'valor': float(valor),
            'email': email,
            'senha': senha,
            'duracao': duracao
        })

        await update.message.reply_text(f"Lara '{nome}' adicionada com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao adicionar lara: {e}")
        await update.message.reply_text("Houve um erro ao adicionar a lara. Tente novamente.")

# Confirmar pagamento
async def confirmar(update: Update, context):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Uso correto: /confirmar <user_id> <valor>")
        return

    user_id = int(context.args[0])
    valor = float(context.args[1])

    if user_id not in pending_recharges:
        await update.message.reply_text(f"Nenhuma solicitação de recarga encontrada para o usuário {user_id}.")
        return

    if pending_recharges[user_id] != valor:
        await update.message.reply_text(f"O valor informado não corresponde à solicitação de recarga.")
        return

    # Confirma o pagamento
    user_balances[user_id] += valor
    del pending_recharges[user_id]  # Remove a recarga pendente

    # Notifica o usuário e o administrador
    await update.message.reply_text(
        f"✅ Recarga de R$ {valor:.2f} confirmada para o usuário {user_id}!"
    )
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Seu pagamento foi confirmado! R$ {valor:.2f} foi adicionado ao seu saldo."
    )

# Configuração principal
def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adicionar", adicionar))
    application.add_handler(CommandHandler("confirmar", confirmar))
    application.add_handler(CallbackQueryHandler(list_logins, pattern='list_logins'))
    application.add_handler(CallbackQueryHandler(process_purchase, pattern='buy_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_recharge_value))
    application.add_handler(CallbackQueryHandler(recharge, pattern='recharge'))

    application.run_polling()

if __name__ == '__main__':
    main()
