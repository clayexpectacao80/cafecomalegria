import flet as ft
import asyncio
from supabase import create_client, Client

# Supabase config
SUPABASE_URL = "https://avgnwbvavkozmgyeaybz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF2Z253YnZhdmtvem1neWVheWJ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxODg1MDIsImV4cCI6MjA2NTc2NDUwMn0.FWXy0ZKh8wsNptAbNE1Dkz2bW_ZgSHY77c_MZb-vZNE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main(page: ft.Page):
    page.title = "Atendimento Cafeteria"
    page.scroll = ft.ScrollMode.ALWAYS
    page.theme_mode = "light"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.padding = 10
    page.window_width = 400
    page.window_height = 750
    page.assets_dir = "assets"  # Para carregar imagens locais (GIF)

    atendentes = ["Clay", "Krys", "Daltino", "Helton"]
    cardapio = ["Pão", "Bolo", "Pastel", "Farofa", "Pão com Queijo Coalho"]
    pedidos_por_mesa = {}
    mesas_ocupadas = {}
    mesas_aguardando_pagamento = {}
    mesa_atual = {"id": None}

    mesa_selecionada_txt = ft.Text("Nenhuma mesa selecionada", size=16, weight="bold", color=ft.Colors.BLUE_GREY_900)
    pedidos_column = ft.Column(scroll=ft.ScrollMode.ALWAYS)
    mesas_grid = ft.ResponsiveRow(run_spacing=5, spacing=5)
    mesa_buttons = []

    def hover_mesa(e: ft.HoverEvent, index: int):
        mesa_id = f"Mesa {index+1}"
        if mesa_id != mesa_atual["id"]:
            mesa_buttons[index].bgcolor = (
                ft.Colors.GREEN_100 if e.data == "true" else ft.Colors.BLUE_100
            )
            page.update()

    async def piscar_mesa(index):
        for _ in range(4):
            mesa_buttons[index].bgcolor = ft.Colors.GREEN_400 if mesa_buttons[index].bgcolor == ft.Colors.GREEN_200 else ft.Colors.GREEN_200
            page.update()
            await asyncio.sleep(0.3)

    def atualizar_pedidos():
        pedidos_column.controls.clear()
        for mesa, pedidos in pedidos_por_mesa.items():
            pedidos_column.controls.append(ft.Text(f"{mesa}:", weight="bold", color=ft.Colors.BLUE_GREY_800))
            for p in pedidos:
                txt = f"- {p['item']} ({p['atendente']})"
                if p["observacao"]:
                    txt += f" - {p['observacao']}"
                pedidos_column.controls.append(ft.Text(txt, size=13))
            pedidos_column.controls.append(
                ft.FilledButton(
                    f"Fechar {mesa}",
                    icon=ft.Icons.CHECK_CIRCLE,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_400, color=ft.Colors.WHITE),
                    on_click=lambda e, m=mesa: fechar_comanda_por_mesa(m),
                )
            )
        page.update()

    def selecionar_mesa(index):
        def handler(e):
            mesa_id = f"Mesa {index+1}"
            if mesa_atual["id"] == mesa_id:
                mesa_atual["id"] = None
                mesa_selecionada_txt.value = "Nenhuma mesa selecionada"
                mesa_buttons[index].bgcolor = ft.Colors.GREEN_800
                if mesa_id not in pedidos_por_mesa:
                    mesas_ocupadas.pop(mesa_id, None)
            else:
                mesa_atual["id"] = mesa_id
                mesa_selecionada_txt.value = f"Mesa Selecionada: {mesa_id}"
                mesas_ocupadas[mesa_id] = True
                for i, m in enumerate(mesa_buttons):
                    m.bgcolor = (
                        ft.Colors.RED_100 if f"Mesa {i+1}" in mesas_aguardando_pagamento else
                        ft.Colors.GREEN_500 if f"Mesa {i+1}" in mesas_ocupadas else
                        ft.Colors.BLUE_100
                    )
                asyncio.run(piscar_mesa(index))
            page.update()
        return handler

    def fechar_comanda_por_mesa(mesa_id):
        mesas_aguardando_pagamento[mesa_id] = pedidos_por_mesa[mesa_id]
        index = int(mesa_id.split()[1]) - 1
        mesa_buttons[index].bgcolor = ft.Colors.RED_300
        atualizar_pedidos()
        page.update()

    def confirmar_pagamento(mesa_id):
        supabase.table("pedidos").update({"confirmado": True}).eq("mesa", mesa_id).execute()
        mesas_aguardando_pagamento.pop(mesa_id, None)
        pedidos_por_mesa.pop(mesa_id, None)
        mesas_ocupadas.pop(mesa_id, None)
        index = int(mesa_id.split()[1]) - 1
        mesa_buttons[index].bgcolor = ft.Colors.BLUE_100
        if mesa_atual["id"] == mesa_id:
            mesa_atual["id"] = None
            mesa_selecionada_txt.value = "Nenhuma mesa selecionada"
        atualizar_pedidos()
        page.go("/")
        page.update()

    def desmarcar_mesa(e):
        mesa_id = mesa_atual["id"]
        if mesa_id:
            index = int(mesa_id.split()[1]) - 1
            mesa_atual["id"] = None
            mesa_selecionada_txt.value = "Nenhuma mesa selecionada"
            if mesa_id not in pedidos_por_mesa:
                mesas_ocupadas.pop(mesa_id, None)
                mesa_buttons[index].bgcolor = ft.Colors.BLUE_100
            page.update()

    def adicionar_pedido(e):
        if not mesa_atual["id"] or not atendente_dropdown.value or not item_dropdown.value:
            return

        pedido = {
            "mesa": mesa_atual["id"],
            "atendente": atendente_dropdown.value,
            "item": item_dropdown.value,
            "observacao": obs_input.value,
            "confirmado": False
        }

        supabase.table("pedidos").insert(pedido).execute()

        if mesa_atual["id"] not in pedidos_por_mesa:
            pedidos_por_mesa[mesa_atual["id"]] = []
        pedidos_por_mesa[mesa_atual["id"]].append(pedido)

        obs_input.value = ""
        atualizar_pedidos()

    # CRIAÇÃO DAS MESAS COM IMAGEM ANIMADA
    for i in range(10):
        btn = ft.Container(
            content=ft.Stack([
                ft.Image(
                    src="img4.gif",
                    width=45,
                    height=45,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(12),
                    opacity=0.95
                ),
                ft.Container(
                    content=ft.Text(
                        f"Mesa {i+1}",
                        size=12,
                        weight="bold",
                        color=ft.Colors.BLACK87,
                        text_align=ft.TextAlign.CENTER,
                        
                    ),
                    alignment=ft.alignment.center
                )
            ]),
            width=60,
            height=40,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=ft.border_radius.all(12),
            shadow=ft.BoxShadow(
                blur_radius=6,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(2, 2)
            ),
            ink=True,
            animate=ft.animation.Animation(duration=300, curve="easeInOut"),
            on_hover=lambda e, b=i: hover_mesa(e, b),
            on_click=selecionar_mesa(i),
        )
        mesa_buttons.append(btn)
        mesas_grid.controls.append(ft.Container(content=btn, col={'xs': 6, 'sm': 3}))

    atendente_dropdown = ft.Dropdown(label="Atendente", options=[ft.dropdown.Option(n) for n in atendentes], dense=True)
    item_dropdown = ft.Dropdown(label="Item", options=[ft.dropdown.Option(i) for i in cardapio], dense=True)
    obs_input = ft.TextField(label="Observação", multiline=True, min_lines=1, max_lines=3)
    adicionar_btn = ft.FilledButton("Adicionar", icon=ft.Icons.ADD, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_400, color=ft.Colors.WHITE), on_click=adicionar_pedido)
    desmarcar_btn = ft.TextButton("Desmarcar mesa", icon=ft.Icons.CLOSE, style=ft.ButtonStyle(color=ft.Colors.RED_400), on_click=desmarcar_mesa)

    def atender_view():
        return ft.View("/", [
            ft.AppBar(title=ft.Text("Atendimento Restaurante"), center_title=True, bgcolor=ft.Colors.BLUE_100, actions=[ft.IconButton(icon=ft.Icons.MANAGE_ACCOUNTS, on_click=lambda e: page.go("/admin"))]),
            ft.Container(
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True,
                    controls=[
                        mesa_selecionada_txt,
                        mesas_grid,
                        ft.Divider(),
                        ft.ResponsiveRow([
                            ft.Container(content=atendente_dropdown, col={"xs": 12, "sm": 4}),
                            ft.Container(content=item_dropdown, col={"xs": 12, "sm": 4}),
                            ft.Container(content=adicionar_btn, col={"xs": 12, "sm": 4}),
                        ], spacing=10),
                        ft.ResponsiveRow([
                            ft.Container(content=obs_input, col={"xs": 12, "sm": 9}),
                            ft.Container(content=desmarcar_btn, col={"xs": 12, "sm": 3})
                        ], spacing=10),
                        ft.Divider(),
                        ft.Text("Pedidos:", size=18, weight="bold", color=ft.Colors.BLUE_GREY_900),
                        pedidos_column
                    ]
                )
            )
        ])

    def admin_view():
        mesas_pagto = []
        for mesa, pedidos in mesas_aguardando_pagamento.items():
            itens = "\n".join([f"- {p['item']} ({p['atendente']})" + (f" - {p['observacao']}" if p['observacao'] else "") for p in pedidos])
            mesas_pagto.append(ft.Card(content=ft.Container(content=ft.Column([
                ft.Text(f"{mesa}", weight="bold"),
                ft.Text(itens),
                ft.FilledButton("Confirmar Pagamento", icon=ft.Icons.PAYMENTS, on_click=lambda e, m=mesa: confirmar_pagamento(m))
            ]), padding=10)))
        return ft.View("/admin", [
            ft.AppBar(title=ft.Text("Área Administrativa"), bgcolor=ft.Colors.BLUE_100, actions=[
                ft.IconButton(icon=ft.Icons.RESTAURANT_MENU, on_click=lambda e: page.go("/"))
            ]),
            ft.Container(
                expand=True,
                padding=10,
                content=ft.Column(mesas_pagto, scroll=ft.ScrollMode.ALWAYS)
            )
        ])

    def route_change(e):
        page.views.clear()
        if page.route == "/admin":
            page.views.append(admin_view())
        else:
            page.views.append(atender_view())
        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main, view=ft.WEB_BROWSER)

