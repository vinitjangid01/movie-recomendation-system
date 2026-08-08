import tkinter as tk
from tkinter import ttk, font
import threading
import math
from recommender import load_data, build_model, get_genres, get_languages, filter_movies, recommend, get_movie_details

# ─── Palette ─────────────────────────────────────────────────────────────────
BG        = "#0A0A0F"
BG2       = "#12121A"
SURFACE   = "#1A1A26"
SURFACE2  = "#22223A"
CARD      = "#2A2A42"
CARD2     = "#32325A"
GOLD      = "#F5C842"
GOLD2     = "#FFE082"
GOLD_DIM  = "#A08020"
ACCENT    = "#E84545"
TEAL      = "#2DD4BF"
PURPLE    = "#A78BFA"
TEXT      = "#F0EEF8"
TEXT2     = "#B0AEC8"
MUTED     = "#6B6988"
BORDER    = "#2E2E48"
GREEN     = "#22C55E"
RED       = "#EF4444"

class CineMatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CineMatch — Movie Recommendation System")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 700)
        self.root.configure(bg=BG)

        self.df = None
        self.similarity = None
        self.all_genres = []
        self.all_languages = []
        self.selected_genre = tk.StringVar(value="All")
        self.selected_lang = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="⏳  Loading 5000+ movies...")
        self.current_movies = []
        self.page = 0
        self.per_page = 20
        self._ac_after = None

        self._setup_fonts()
        self._build_layout()
        self._load_async()

    # ── Fonts ─────────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.font_title  = ("Georgia", 22, "bold")
        self.font_sub    = ("Segoe UI", 11)
        self.font_h2     = ("Georgia", 14, "bold")   
        self.font_body   = ("Segoe UI", 12)
        self.font_small  = ("Segoe UI", 10)
        self.font_card   = ("Helvetica", 10, "bold")
        self.font_tag    = ("Segoe UI", 10)
        self.font_status = ("Segoe UI", 10)

    
    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # ── Top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=SURFACE, height=64)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="🎬", font=("Helvetica", 26),
                 bg=SURFACE, fg=GOLD).pack(side="left", padx=(18, 4), pady=10)
        tk.Label(topbar, text="CineMatch", font=self.font_title,
                 bg=SURFACE, fg=GOLD).pack(side="left", pady=10)
        tk.Label(topbar, text="  ·  5000+ movies  ·  NLP Powered  ·  Cosine Similarity",
                 font=self.font_sub, bg=SURFACE, fg=MUTED).pack(side="left", pady=10)

        self.status_lbl = tk.Label(topbar, textvariable=self.status_var,
                                   font=self.font_status, bg=SURFACE, fg=MUTED)
        self.status_lbl.pack(side="right", padx=18)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── Main body ─────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # Left sidebar
        self.sidebar = tk.Frame(body, bg=BG2, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # Main content
        self.main = tk.Frame(body, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self._build_main()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        pad = {"padx": 14, "pady": 0}

        # Search box
        tk.Label(self.sidebar, text="SEARCH", font=("Helvetica", 8, "bold"),
                 bg=BG2, fg=MUTED).pack(anchor="w", padx=14, pady=(18, 5))

        search_wrap = tk.Frame(self.sidebar, bg=BORDER, padx=1, pady=1)
        search_wrap.pack(fill="x", padx=14)
        search_inner = tk.Frame(search_wrap, bg=SURFACE)
        search_inner.pack(fill="x")

        self.search_entry = tk.Entry(search_inner, textvariable=self.search_var,
                                     bg=SURFACE, fg=TEXT, insertbackground=GOLD,
                                     font=self.font_body, relief="flat", bd=0,
                                     highlightthickness=0)
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        self.search_entry.bind("<KeyRelease>", self._on_key)

        # Autocomplete
        self.ac_frame = tk.Frame(self.sidebar, bg=CARD2)
        self.ac_list = tk.Listbox(self.ac_frame, bg=CARD2, fg=TEXT,
                                  font=("Helvetica", 10), relief="flat",
                                  selectbackground=GOLD, selectforeground=BG,
                                  activestyle="none", bd=0, highlightthickness=0,
                                  height=6)
        self.ac_list.pack(fill="both", expand=True)
        self.ac_list.bind("<<ListboxSelect>>", self._on_ac_select)
        self.ac_list.bind("<Return>", self._on_ac_select)
        self.search_var.trace_add("write", self._update_ac)

        btn_row = tk.Frame(self.sidebar, bg=BG2)
        btn_row.pack(fill="x", padx=14, pady=(6, 0))

        self.btn_search = tk.Button(btn_row, text="🔍  Search",
                                    bg=GOLD, fg=BG, font=("Helvetica", 10, "bold"),
                                    relief="flat", bd=0, padx=12, pady=7,
                                    activebackground=GOLD2, activeforeground=BG,
                                    cursor="hand2", command=self._do_search)
        self.btn_search.pack(side="left", fill="x", expand=True)

        tk.Button(btn_row, text="✕", bg=SURFACE2, fg=MUTED,
                  font=("Helvetica", 10), relief="flat", bd=0,
                  padx=10, pady=7, activebackground=CARD,
                  cursor="hand2", command=self._clear_search).pack(side="left", padx=(6, 0))

        # Divider
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=14, pady=14)

        # Language filter
        tk.Label(self.sidebar, text="LANGUAGE", font=("Helvetica", 8, "bold"),
                 bg=BG2, fg=MUTED).pack(anchor="w", padx=14, pady=(0, 8))

        self.lang_frame = tk.Frame(self.sidebar, bg=BG2)
        self.lang_frame.pack(fill="x", padx=14)

        self._add_filter_chip(self.lang_frame, "All", self.selected_lang,
                              self._on_filter_change, is_lang=True)
        for lang in ["Hindi", "English"]:
            self._add_filter_chip(self.lang_frame, lang, self.selected_lang,
                                  self._on_filter_change, is_lang=True)

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=14, pady=14)

        # Genre filter
        tk.Label(self.sidebar, text="GENRE", font=("Helvetica", 8, "bold"),
                 bg=BG2, fg=MUTED).pack(anchor="w", padx=14, pady=(0, 8))

        self.genre_scroll_frame = tk.Frame(self.sidebar, bg=BG2)
        self.genre_scroll_frame.pack(fill="both", expand=True, padx=14)

        genre_canvas = tk.Canvas(self.genre_scroll_frame, bg=BG2,
                                 highlightthickness=0, bd=0)
        genre_scroll = ttk.Scrollbar(self.genre_scroll_frame, orient="vertical",
                                     command=genre_canvas.yview)
        self.genre_inner = tk.Frame(genre_canvas, bg=BG2)
        self.genre_inner.bind("<Configure>",
                              lambda e: genre_canvas.configure(
                                  scrollregion=genre_canvas.bbox("all")))
        genre_canvas.create_window((0, 0), window=self.genre_inner, anchor="nw")
        genre_canvas.configure(yscrollcommand=genre_scroll.set)
        genre_canvas.pack(side="left", fill="both", expand=True)
        genre_scroll.pack(side="right", fill="y")

        self._add_filter_chip(self.genre_inner, "All", self.selected_genre,
                              self._on_filter_change)

        PRESET_GENRES = ["Action", "Drama", "Comedy", "Thriller", "Romance",
                         "Sci-Fi", "Horror", "Crime", "Biography", "Adventure",
                         "Mystery", "Animation", "Fantasy", "Music", "Sport",
                         "History", "War", "Western", "Family", "Documentary"]
        for g in PRESET_GENRES:
            self._add_filter_chip(self.genre_inner, g, self.selected_genre,
                                  self._on_filter_change)

    def _add_filter_chip(self, parent, label, var, callback, is_lang=False):
        colors = {
            "Action": "#E84545", "Drama": "#A78BFA", "Comedy": "#FBBF24",
            "Thriller": "#F97316", "Romance": "#EC4899", "Sci-Fi": "#2DD4BF",
            "Horror": "#EF4444", "Crime": "#8B5CF6", "Biography": "#10B981",
            "Adventure": "#F59E0B", "Mystery": "#6366F1", "Animation": "#06B6D4",
            "Fantasy": "#8B5CF6", "Music": "#EC4899", "Sport": "#22C55E",
            "History": "#D97706", "War": "#6B7280", "Western": "#B45309",
            "Family": "#14B8A6", "Documentary": "#64748B",
            "Hindi": GOLD, "English": TEAL, "All": MUTED
        }
        color = colors.get(label, MUTED)

        frame = tk.Frame(parent, bg=BG2)
        frame.pack(fill="x", pady=1)

        btn = tk.Button(
            frame, text=label,
            font=self.font_small,
            bg=BG2, fg=TEXT2,
            relief="flat", bd=0,
            padx=10, pady=5,
            anchor="w", cursor="hand2",
            activebackground=SURFACE2,
            command=lambda: self._select_filter(var, label, callback)
        )
        btn.pack(fill="x")

        dot = tk.Label(frame, text="●", font=("Helvetica", 7),
                       bg=BG2, fg=color)
        dot.place(x=4, y=7)

        setattr(btn, "_label", label)
        setattr(btn, "_color", color)

        if not hasattr(self, "_filter_btns"):
            self._filter_btns = {}
        key = ("lang" if is_lang else "genre") + "_" + label
        self._filter_btns[key] = (btn, dot, is_lang, label)

        if label == "All":
            btn.config(fg=GOLD, font=("Helvetica", 9, "bold"))

    def _select_filter(self, var, label, callback):
        var.set(label)
        callback()
        self._update_chip_styles()

    def _update_chip_styles(self):
        if not hasattr(self, "_filter_btns"):
            return
        g = self.selected_genre.get()
        l = self.selected_lang.get()
        for key, (btn, dot, is_lang, label) in self._filter_btns.items():
            selected = (label == l) if is_lang else (label == g)
            if selected:
                btn.config(bg=SURFACE2, fg=GOLD, font=("Helvetica", 9, "bold"))
                dot.config(bg=SURFACE2)
            else:
                btn.config(bg=BG2, fg=TEXT2, font=self.font_small)
                dot.config(bg=BG2)

    # ── Main content ──────────────────────────────────────────────────────────
    def _build_main(self):
        # Top bar inside main
        self.main_top = tk.Frame(self.main, bg=BG, pady=12)
        self.main_top.pack(fill="x", padx=20)

        self.section_title = tk.Label(self.main_top, text="🎬  All Movies",
                                      font=self.font_h2, bg=BG, fg=TEXT)
        self.section_title.pack(side="left")

        self.count_lbl = tk.Label(self.main_top, text="",
                                  font=self.font_small, bg=BG, fg=MUTED)
        self.count_lbl.pack(side="right")

        # Movie grid area with scrollbar
        grid_outer = tk.Frame(self.main, bg=BG)
        grid_outer.pack(fill="both", expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(grid_outer, bg=BG, highlightthickness=0, bd=0)
        self.vscroll = ttk.Scrollbar(grid_outer, orient="vertical",
                                     command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscroll.set)
        self.vscroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self.grid_win = self.canvas.create_window((0, 0), window=self.grid_frame,
                                                   anchor="nw")

        self.grid_frame.bind("<Configure>",
                             lambda e: self.canvas.configure(
                                 scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(
                             self.grid_win, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(
                                 int(-1 * (e.delta / 120)), "units"))

        # Pagination
        pg_bar = tk.Frame(self.main, bg=SURFACE, pady=8)
        pg_bar.pack(fill="x", side="bottom")

        self.btn_prev = tk.Button(pg_bar, text="◀  Prev",
                                  bg=SURFACE2, fg=TEXT2, font=self.font_small,
                                  relief="flat", bd=0, padx=14, pady=6,
                                  cursor="hand2", activebackground=CARD,
                                  command=self._prev_page)
        self.btn_prev.pack(side="left", padx=(18, 8))

        self.page_lbl = tk.Label(pg_bar, text="Page 1", font=self.font_small,
                                 bg=SURFACE, fg=MUTED)
        self.page_lbl.pack(side="left")

        self.btn_next = tk.Button(pg_bar, text="Next  ▶",
                                  bg=SURFACE2, fg=TEXT2, font=self.font_small,
                                  relief="flat", bd=0, padx=14, pady=6,
                                  cursor="hand2", activebackground=CARD,
                                  command=self._next_page)
        self.btn_next.pack(side="left", padx=8)

    # ── Movie card ────────────────────────────────────────────────────────────
    def _render_grid(self, movies):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        COLS = 4
        for i, movie in enumerate(movies):
            row = i // COLS
            col = i % COLS
            self._make_card(self.grid_frame, movie, row, col)

        self.canvas.yview_moveto(0)

    def _make_card(self, parent, movie, row, col):
        title = movie.get("title", "")
        genres = movie.get("genres", "")
        lang = movie.get("language", "")
        year = movie.get("year", "")
        rating = movie.get("rating", "")
        score = movie.get("score", None)

        card = tk.Frame(parent, bg=CARD, cursor="hand2",
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=GOLD)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        card.bind("<Enter>", lambda e, c=card: self._card_hover(c, True))
        card.bind("<Leave>", lambda e, c=card: self._card_hover(c, False))
        card.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        # Genre color stripe
        genre_colors = {
            "Action": "#E84545", "Drama": "#A78BFA", "Comedy": "#FBBF24",
            "Thriller": "#F97316", "Romance": "#EC4899", "Sci-Fi": "#2DD4BF",
            "Horror": "#EF4444", "Crime": "#8B5CF6", "Biography": "#10B981",
            "Adventure": "#F59E0B", "Mystery": "#6366F1", "Animation": "#06B6D4",
            "Fantasy": "#8B5CF6", "Music": "#EC4899", "Sport": "#22C55E"
        }
        first_genre = genres.split(",")[0].strip() if genres else ""
        stripe_color = genre_colors.get(first_genre, GOLD_DIM)

        stripe = tk.Frame(card, bg=stripe_color, height=4)
        stripe.pack(fill="x")
        stripe.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        inner = tk.Frame(card, bg=CARD, pady=10, padx=10)
        inner.pack(fill="both", expand=True)
        inner.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        # Language badge + rating
        top_row = tk.Frame(inner, bg=CARD)
        top_row.pack(fill="x")
        top_row.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        lang_col = "#FBBF24" if lang == "Hindi" else "#2DD4BF"
        lang_badge = tk.Label(top_row, text=lang,
                              font=self.font_tag, bg=lang_col,
                              fg=BG, padx=5, pady=1)
        lang_badge.pack(side="left")
        lang_badge.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        if score is not None:
            score_lbl = tk.Label(top_row, text=f"  {score}% match",
                                 font=self.font_tag, bg=CARD, fg=TEAL)
            score_lbl.pack(side="left")
            score_lbl.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        if rating:
            try:
                r = float(rating)
                star = "★" * int(r / 2) + "☆" * (5 - int(r / 2))
                rat_lbl = tk.Label(top_row, text=f"  {r:.1f}",
                                   font=self.font_tag, bg=CARD, fg=GOLD)
                rat_lbl.pack(side="right")
                rat_lbl.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))
            except:
                pass

        # Title
        short_title = title if len(title) <= 36 else title[:33] + "…"
        title_lbl = tk.Label(inner, text=short_title,
                             font=("Helvetica", 10, "bold"),
                             bg=CARD, fg=TEXT, anchor="w",
                             wraplength=180, justify="left")
        title_lbl.pack(fill="x", pady=(6, 2))
        title_lbl.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

        # Year + genre
        meta = f"{year}  ·  {first_genre}" if year else first_genre
        meta_lbl = tk.Label(inner, text=meta, font=self.font_tag,
                            bg=CARD, fg=MUTED, anchor="w")
        meta_lbl.pack(fill="x")
        meta_lbl.bind("<Button-1>", lambda e, m=movie: self._open_detail(m))

    def _card_hover(self, card, entering):
        color = CARD2 if entering else CARD
        bc = GOLD if entering else BORDER
        card.configure(bg=color, highlightbackground=bc)
        for w in card.winfo_children():
            try:
                w.configure(bg=color)
                for ww in w.winfo_children():
                    try:
                        if ww.cget("bg") == CARD or ww.cget("bg") == CARD2:
                            ww.configure(bg=color)
                    except:
                        pass
            except:
                pass

    # ── Movie detail popup ────────────────────────────────────────────────────
    def _open_detail(self, movie):
        title = movie.get("title", "")
        detail = get_movie_details(title, self.df) if self.df is not None else movie

        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("640x580")
        popup.configure(bg=BG)
        popup.grab_set()

        # Header
        hdr = tk.Frame(popup, bg=SURFACE, pady=16)
        hdr.pack(fill="x")

        tk.Label(hdr, text="🎬", font=("Helvetica", 28),
                 bg=SURFACE, fg=GOLD).pack(side="left", padx=(18, 8))

        hdr_text = tk.Frame(hdr, bg=SURFACE)
        hdr_text.pack(side="left", fill="x", expand=True)

        tk.Label(hdr_text, text=detail.get("title", title),
                 font=("Georgia", 16, "bold"),
                 bg=SURFACE, fg=GOLD, anchor="w",
                 wraplength=440).pack(anchor="w")

        year = detail.get("year", "")
        lang = detail.get("language", "")
        rating = detail.get("rating", "")
        meta_str = "  ·  ".join(filter(None, [str(year) if year else "", lang,
                                               f"⭐ {rating}" if rating else ""]))
        tk.Label(hdr_text, text=meta_str,
                 font=("Helvetica", 10),
                 bg=SURFACE, fg=TEXT2).pack(anchor="w", pady=(4, 0))

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(popup, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Genre tags
        genres = detail.get("genres", "")
        if genres:
            genre_row = tk.Frame(body, bg=BG)
            genre_row.pack(anchor="w", pady=(0, 12))
            for g in genres.split(","):
                g = g.strip()
                if g:
                    tk.Label(genre_row, text=g, font=self.font_tag,
                             bg=SURFACE2, fg=TEAL,
                             padx=8, pady=3).pack(side="left", padx=(0, 6))

        def _section(parent, label, value):
            if not value or str(value).strip() in ("", "nan", "N/A"):
                return
            f = tk.Frame(parent, bg=BG, pady=4)
            f.pack(fill="x")
            tk.Label(f, text=label, font=("Helvetica", 9, "bold"),
                     bg=BG, fg=MUTED, width=10, anchor="w").pack(side="left")
            tk.Label(f, text=str(value), font=("Helvetica", 10),
                     bg=BG, fg=TEXT, wraplength=460, justify="left",
                     anchor="w").pack(side="left", fill="x", expand=True)

        _section(body, "Director", detail.get("director", ""))
        _section(body, "Cast", detail.get("cast", ""))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=10)

        # Story / Overview
        overview = detail.get("overview", "")
        if overview and overview.strip():
            tk.Label(body, text="Story", font=("Helvetica", 11, "bold"),
                     bg=BG, fg=GOLD).pack(anchor="w", pady=(0, 6))

            story_text = tk.Text(body, font=("Helvetica", 10),
                                 bg=SURFACE, fg=TEXT2, relief="flat",
                                 bd=0, wrap="word", height=8,
                                 padx=12, pady=10,
                                 highlightthickness=0)
            story_text.insert("1.0", overview)
            story_text.config(state="disabled")
            story_text.pack(fill="x")

        # Recommend button
        def _find_similar():
            popup.destroy()
            self.search_var.set(title)
            self._do_recommend(title)

        btn_row = tk.Frame(popup, bg=SURFACE, pady=12)
        btn_row.pack(fill="x", side="bottom")

        tk.Button(btn_row, text="🔍  Find Similar Movies",
                  bg=GOLD, fg=BG, font=("Helvetica", 11, "bold"),
                  relief="flat", bd=0, padx=20, pady=9,
                  activebackground=GOLD2, activeforeground=BG,
                  cursor="hand2", command=_find_similar).pack(side="left", padx=18)

        tk.Button(btn_row, text="Close",
                  bg=SURFACE2, fg=TEXT2, font=("Helvetica", 10),
                  relief="flat", bd=0, padx=16, pady=9,
                  cursor="hand2", activebackground=CARD,
                  command=popup.destroy).pack(side="left")

    # ── Search & Filter logic ─────────────────────────────────────────────────
    def _on_key(self, event):
        if event.keysym == "Return":
            self._do_search()

    def _update_ac(self, *args):
        if self._ac_after:
            self.root.after_cancel(self._ac_after)
        self._ac_after = self.root.after(200, self._show_ac)

    def _show_ac(self):
        q = self.search_var.get().strip().lower()
        if len(q) < 2 or self.df is None:
            self.ac_frame.pack_forget()
            return
        matches = self.df[self.df["title"].str.lower().str.contains(q, na=False, regex=False)]["title"].head(8).tolist()
        if not matches:
            self.ac_frame.pack_forget()
            return
        self.ac_list.delete(0, "end")
        for m in matches:
            self.ac_list.insert("end", "  " + m)
        self.ac_frame.pack(fill="x", padx=14, pady=(0, 4))

    def _on_ac_select(self, event):
        sel = self.ac_list.curselection()
        if sel:
            val = self.ac_list.get(sel[0]).strip()
            self.search_var.set(val)
            self.ac_frame.pack_forget()
            self._do_recommend(val)

    def _do_search(self):
        q = self.search_var.get().strip()
        self.ac_frame.pack_forget()
        if q and self.df is not None:
            self._do_recommend(q)
        else:
            self._apply_filter()

    def _clear_search(self):
        self.search_var.set("")
        self.ac_frame.pack_forget()
        self._apply_filter()

    def _on_filter_change(self):
        self._update_chip_styles()
        q = self.search_var.get().strip()
        if q and self.df is not None:
            self._do_recommend(q)
        else:
            self._apply_filter()

    def _apply_filter(self):
        if self.df is None:
            return
        g = self.selected_genre.get()
        l = self.selected_lang.get()
        filtered = filter_movies(self.df, genre=g if g != "All" else None,
                                 language=l if l != "All" else None)
        self.current_movies = filtered.to_dict("records")
        self.page = 0
        self.section_title.config(text="🎬  All Movies")
        self._render_page()

    def _do_recommend(self, title):
        if self.df is None or self.similarity is None:
            return
        g = self.selected_genre.get()
        l = self.selected_lang.get()
        results = recommend(title, self.df, self.similarity, top_n=36,
                            genre_filter=g if g != "All" else None,
                            lang_filter=l if l != "All" else None)
        if results:
            self.current_movies = results
            self.page = 0
            short = title[:30] + "…" if len(title) > 30 else title
            self.section_title.config(text=f'🎯  Similar to "{short}"')
        else:
            self._apply_filter()
            self.section_title.config(text=f'❌  No matches — showing all')
        self._render_page()

    def _render_page(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_movies = self.current_movies[start:end]
        total_pages = max(1, math.ceil(len(self.current_movies) / self.per_page))
        self.page_lbl.config(text=f"Page {self.page + 1} of {total_pages}")
        self.count_lbl.config(text=f"{len(self.current_movies):,} movies")
        self._render_grid(page_movies)

    def _prev_page(self):
        if self.page > 0:
            self.page -= 1
            self._render_page()

    def _next_page(self):
        total = math.ceil(len(self.current_movies) / self.per_page)
        if self.page < total - 1:
            self.page += 1
            self._render_page()

    # ── Loading ───────────────────────────────────────────────────────────────
    def _load_async(self):
        def _load():
            self.df = load_data()
            self.root.after(0, lambda: self.status_var.set("⚙️  Building NLP model..."))
            self.similarity = build_model(self.df)
            self.all_genres = get_genres(self.df)
            self.all_languages = get_languages(self.df)
            self.root.after(0, self._on_ready)
        threading.Thread(target=_load, daemon=True).start()

    def _on_ready(self):
        n = len(self.df)
        self.status_var.set(f"✅  {n:,} movies ready")
        self._apply_filter()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = CineMatchApp(root)
    root.mainloop()
