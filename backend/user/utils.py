def generate_avatar_url(name):
    base_url = "https://ui-avatars.com/api/"
    params = "?"
    params += "name=" + name.replace(" ", "+")
    params += "&background=random"
    params += "&color=fff"
    params += "&length=2"
    params += "&bold=true"
    params += "&size=128"
    return base_url + params