def generate_avatar_url(full_name):
    try:
        base_url = "https://ui-avatars.com/api/"
        name_parts = full_name.split(" ")
        
        if len(name_parts) > 1:
            formatted_name = name_parts[0] + " " + name_parts[-1]

        formatted_name = formatted_name.replace(".", " ").title()
        params = "?"
        params += "name=" + formatted_name.replace(" ", "+")
        params += "&background=random"
        params += "&color=fff"
        params += "&length=2"
        params += "&bold=true"
        params += "&size=128"
        return base_url + params
    except Exception as e:
        print(f"Error generating avatar URL: {e}")
        return None
