#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define WORD(p, n) (*(u32 *)((u8 *)(p) + (n)))
#define HALF(p, n) (*(u16 *)((u8 *)(p) + (n)))
#define PTR(p, n) (*(void **)((u8 *)(p) + (n)))

typedef struct {
    u32 id;
    u8 neighbor[4];
} NavEntry;

typedef struct {
    u32 pinyinNum;
    u32 candidateOffset;
    u32 maxCandidateNum;
    u32 reserved;
} PinyinHeader;

typedef struct {
    u32 pinyin;
    u16 candidateOffset;
    u16 candidateNum;
} PinyinEntry;

typedef struct {
    u32 initialized;
    u32 letterCount;
    u32 candidateCount;
    u32 page;
    u32 kana;
    u8 letters[8];
    const u16 *candidates;
    u16 original[2][65];
    void *nav;
    NavEntry *originalNav;
    NavEntry navigation[78];
} PinyinState;

extern const PinyinHeader *Pinyin_GetTable(void);
#ifdef PINYIN_ORAS
extern void *Original_Factory(void *object, void *parameters);
#else
extern void *Original_Constructor(void *main, void *parameters);
#endif
extern int Original_Action(void *main, int event);
extern int Original_Refresh(void *main, int layout, int mode, int count);
extern int Native_Commit(void *main, int key);

static PinyinState *GetState(void *main)
{
    return (PinyinState *)((u8 *)main + 0x84);
}

static u16 *GetTable(void *main, int page)
{
    void *tables = PTR(PTR(main, 0x64), 8);
    return (u16 *)PTR(tables, page * 4) + 2;
}

static int IsPinyin(void *main)
{
    return WORD(main, 0x4c) == 0 && WORD(main, 0x50) == 0;
}

static void Reset(PinyinState *state)
{
    state->letterCount = 0;
    state->candidateCount = 0;
    state->candidates = 0;
    state->page = 0;
}

static void FindCandidates(PinyinState *state)
{
    const PinyinHeader *header = Pinyin_GetTable();
    const PinyinEntry *entries = (const PinyinEntry *)(header + 1);
    int left = 0;
    int right = header->pinyinNum - 1;
    u32 value = 0;
    state->candidateCount = 0;
    state->candidates = 0;
    state->page = 0;
    if (!state->letterCount)
        return;
    for (u32 i = 0; i < state->letterCount; ++i)
        value |= ((state->letters[i] - 'a' + 1) & 31) << (25 - i * 5);
    while (left <= right) {
        int middle = (left + right) / 2;
        const PinyinEntry *entry = &entries[middle];
        if (entry->pinyin == value) {
            state->candidates = (const u16 *)((const u8 *)header + header->candidateOffset)
                                + entry->candidateOffset;
            state->candidateCount = entry->candidateNum;
            return;
        }
        if (entry->pinyin < value)
            left = middle + 1;
        else
            right = middle - 1;
    }
}

static int ValidKey(PinyinState *state, u32 key)
{
    if (key < 26 || key >= 65)
        return 1;
    if (key == 37)
        return state->page > 0;
    if (key == 38)
        return (state->page + 1) * 26 < state->candidateCount;
    if (key >= 39)
        return state->page * 26 + key - 39 < state->candidateCount;
    return 0;
}

static void UpdateNavigation(void *main, PinyinState *state)
{
    void *controller = PTR(PTR(main, 0x64), 4);
    void *nav = PTR(controller, 0x18);
    if (state->nav != nav || PTR(nav, 8) != state->navigation) {
        state->nav = nav;
        state->originalNav = PTR(nav, 8);
    }
    if (!IsPinyin(main)) {
        if (PTR(nav, 8) == state->navigation)
            PTR(nav, 8) = state->originalNav;
        return;
    }
    u32 count = WORD(nav, 16);
    for (u32 i = 0; i < count; ++i) {
        state->navigation[i] = state->originalNav[i];
        for (u32 direction = 0; direction < 4; ++direction) {
            u32 next = state->originalNav[i].neighbor[direction];
            for (u32 step = 0; step < count && next < count; ++step) {
                if (ValidKey(state, state->originalNav[next].id))
                    break;
                next = state->originalNav[next].neighbor[direction];
            }
            state->navigation[i].neighbor[direction] = next;
        }
    }
    PTR(nav, 8) = state->navigation;
}

static void BuildRows(void *main)
{
    PinyinState *state = GetState(main);
    if (!state->initialized) {
        for (int page = 0; page < 2; ++page) {
            u16 *table = GetTable(main, page);
            for (int i = 0; i < 65; ++i)
                state->original[page][i] = table[i];
        }
        state->initialized = 1;
    }
    if (IsPinyin(main)) {
        u16 *table = GetTable(main, 0);
        for (int i = 0; i < 65; ++i)
            table[i] = 0x3000;
        for (int i = 0; i < 26; ++i)
            table[i] = 'a' + i;
        for (u32 i = 0; i < state->letterCount; ++i)
            table[27 + i] = state->letters[i];
        if (state->candidateCount > 26) {
            u32 pages = (state->candidateCount + 25) / 26;
            table[34] = '1' + state->page;
            table[35] = '/';
            table[36] = '0' + pages;
            table[37] = state->page ? '<' : 0x3000;
            table[38] = state->page + 1 < pages ? '>' : 0x3000;
        }
        for (u32 i = 0; i < 26; ++i) {
            u32 index = state->page * 26 + i;
            if (index < state->candidateCount)
                table[39 + i] = state->candidates[index];
        }
    } else if (WORD(main, 0x4c) == 0 && WORD(main, 0x50) == 1) {
        u16 *table = GetTable(main, 1);
        for (int i = 0; i < 65; ++i)
            table[i] = state->original[state->kana][i];
    }
    UpdateNavigation(main, state);
}

#ifdef PINYIN_ORAS
void *Pinyin_Factory(void *object, void *parameters)
{
    void *result = Original_Factory(object, parameters);
    void *main = PTR(result, 0x24);
#else
void *Pinyin_Constructor(void *main, void *parameters)
{
    void *result = Original_Constructor(main, parameters);
#endif
    u8 *bytes = (u8 *)GetState(main);
    for (u32 i = 0; i < sizeof(PinyinState); ++i)
        bytes[i] = 0;
    WORD(main, 0x4c) = 0;
    WORD(main, 0x50) = 0;
    return result;
}

int Pinyin_Refresh(void *main, int layout, int mode, int count)
{
    BuildRows(main);
    return Original_Refresh(main, layout, mode, count);
}

int Pinyin_Action(void *main, int event)
{
    PinyinState *state = GetState(main);
    if (IsPinyin(main)) {
        if (event >= 24 && event < 89) {
            u32 key = event - 24;
            if (!ValidKey(state, key))
                return 4;
            if (key < 26) {
                if (state->letterCount < 6) {
                    state->letters[state->letterCount++] = 'a' + key;
                    FindCandidates(state);
                }
            } else if (key == 37) {
                --state->page;
            } else if (key == 38) {
                ++state->page;
            } else {
                Native_Commit(main, key);
                Reset(state);
            }
            Pinyin_Refresh(main, 1, 0, 65);
            return 4;
        }
        if ((event == 14 || event == 15) && state->letterCount) {
            --state->letterCount;
            FindCandidates(state);
            Pinyin_Refresh(main, 1, 0, 65);
            return 4;
        }
    }
    if (event == 10 && WORD(main, 0x4c) == 0 && WORD(main, 0x50) == 1) {
        state->kana ^= 1;
        Pinyin_Refresh(main, 1, 0, 65);
        return 4;
    }
    if (event >= 9 && event <= 12)
        Reset(state);
    return Original_Action(main, event);
}
