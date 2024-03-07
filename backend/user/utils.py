def generate_avatar_url(email):
    try:
        base_url = "https://ui-avatars.com/api/"
        name, _ = email.split("@")[0].split(".")
        formatted_name = name.replace(".", " ").title()
        params = "?"
        params += "name=" + formatted_name.replace(" ", "+")
        params += "&background=random"
        params += "&color=fff"
        params += "&length=2"
        params += "&bold=true"
        params += "&size=128"
        return base_url + params
    except:
        return None
