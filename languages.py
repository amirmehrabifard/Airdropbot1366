def get_text(key, lang='en'):
    texts = {
        'welcome': {
            'en': "Welcome! Join our channel @{channel} and click below.",
            'fa': "خوش آمدی! لطفا در کانال @{channel} عضو شو و روی دکمه زیر بزن.",
            'ar': "مرحبًا! انضم إلى قناتنا @{channel} واضغط أدناه.",
            'zh': "欢迎！请加入频道 @{channel} 并点击下方。",
            'ru': "Добро пожаловать! Присоединяйтесь к нашему каналу @{channel} и нажмите ниже.",
            'fr': "Bienvenue ! Rejoignez notre chaîne @{channel} et cliquez ci-dessous."
        },
        'joined_btn': {
            'en': "Joined Channel ✅", 'fa': "عضو شدم ✅", 'ar': "انضممت ✅",
            'zh': "我加入了 ✅", 'ru': "Вступил ✅", 'fr': "Rejoint ✅"
        },
        'check_btn': {
            'en': "Check ✅", 'fa': "بررسی ✅", 'ar': "تحقق ✅",
            'zh': "检查 ✅", 'ru': "Проверить ✅", 'fr': "Vérifier ✅"
        },
        'joined_success': {
            'en': "Great! You’ve joined the channel.",
            'fa': "عالی! تو عضو کانال شدی.",
            'ar': "رائع! لقد انضممت.",
            'zh': "太棒了！你已加入。",
            'ru': "Отлично! Вы присоединились.",
            'fr': "Parfait ! Vous avez rejoint."
        },
        'not_joined': {
            'en': "You haven’t joined yet.",
            'fa': "هنوز عضو نشدی.",
            'ar': "لم تنضم بعد.",
            'zh': "你还没加入。",
            'ru': "Вы еще не присоединились.",
            'fr': "Vous n'avez pas encore rejoint."
        },
        'ask_wallet': {
            'en': "Now send me your BNB Smart Chain wallet address.",
            'fa': "حالا آدرس کیف پول شبکه BNB خود را ارسال کن.",
            'ar': "أرسل عنوان محفظتك الآن.",
            'zh': "现在发送你的 BNB 钱包地址。",
            'ru': "Отправьте адрес своего кошелька.",
            'fr': "Envoyez votre adresse de portefeuille."
        },
        'wallet_saved': {
            'en': "Wallet address saved successfully!",
            'fa': "آدرس کیف پول با موفقیت ذخیره شد!",
            'ar': "تم حفظ العنوان بنجاح!",
            'zh': "地址保存成功！",
            'ru': "Адрес сохранен!",
            'fr': "Adresse enregistrée !"
        },
        'referral_link': {
            'en': "Your referral link:\n",
            'fa': "لینک دعوت شما:\n",
            'ar': "رابط الدعوة الخاص بك:\n",
            'zh': "你的邀请链接：\n",
            'ru': "Ваша реферальная ссылка:\n",
            'fr': "Votre lien de parrainage :\n"
        }
    }
    return texts.get(key, {}).get(lang, texts.get(key, {}).get('en', '...'))
