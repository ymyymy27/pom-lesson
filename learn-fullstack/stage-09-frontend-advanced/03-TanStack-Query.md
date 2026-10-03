# 第 03 节：TanStack Query（React Query）

## 一、为什么需要 TanStack Query？

手动管理服务端状态（loading / error / data / 缓存 / 重新请求）代码冗长且容易出错。TanStack Query 自动处理：

- **缓存** — 相同请求自动复用缓存
- **后台刷新** — 数据过期后自动后台更新
- **去重** — 多个组件请求同一数据，只发一次请求
- **自动重试** — 失败自动重试
- **乐观更新** — 先更新 UI，再请求 API
- **分页/无限滚动** — 内置支持

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

---

## 二、配置

```tsx
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 60 * 1000,       // 数据 60 秒内视为新鲜
            retry: 2,                    // 失败重试 2 次
            refetchOnWindowFocus: false, // 窗口聚焦时不自动刷新
        },
    },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
    <QueryClientProvider client={queryClient}>
        <BrowserRouter>
            <App />
        </BrowserRouter>
        <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
);
```

---

## 三、useQuery — 查询数据

```tsx
import { useQuery } from '@tanstack/react-query';
import { taskService } from '@/services/taskService';

function TaskListPage() {
    const [status, setStatus] = useState('all');
    const [page, setPage] = useState(1);
    
    const { data, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['tasks', { status, page }],  // 缓存键（依赖变化时自动重新请求）
        queryFn: () => taskService.getList({
            status: status !== 'all' ? status : undefined,
            page,
        }).then(res => res.data),
    });
    
    if (isLoading) return <Spinner />;
    if (isError) return <ErrorMessage message={error.message} onRetry={refetch} />;
    
    return (
        <div>
            <StatusFilter value={status} onChange={(v) => { setStatus(v); setPage(1); }} />
            <TaskList tasks={data?.results ?? []} />
            <Pagination
                page={page}
                total={data?.count ?? 0}
                onChange={setPage}
            />
        </div>
    );
}

// 任务详情
function TaskDetailPage() {
    const { id } = useParams<{ id: string }>();
    
    const { data: task, isLoading } = useQuery({
        queryKey: ['tasks', Number(id)],
        queryFn: () => taskService.getById(Number(id)).then(res => res.data),
        enabled: !!id,  // id 存在时才请求
    });
    
    if (isLoading) return <Spinner />;
    if (!task) return <NotFound />;
    
    return <TaskDetail task={task} />;
}

// 任务统计
function TaskStats() {
    const { data: stats } = useQuery({
        queryKey: ['tasks', 'statistics'],
        queryFn: () => taskService.getStatistics().then(res => res.data),
        staleTime: 5 * 60 * 1000,  // 5 分钟内不重新请求
    });
    
    return <StatsPanel stats={stats} />;
}
```

---

## 四、useMutation — 修改数据

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function CreateTaskForm() {
    const queryClient = useQueryClient();
    
    const createMutation = useMutation({
        mutationFn: (data: CreateTaskRequest) => taskService.create(data).then(res => res.data),
        onSuccess: () => {
            // 创建成功后，使任务列表缓存失效（自动重新请求）
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
        onError: (error) => {
            console.error('创建失败:', error);
        },
    });
    
    const handleSubmit = (data: CreateTaskRequest) => {
        createMutation.mutate(data);
    };
    
    return (
        <form onSubmit={...}>
            {/* 表单字段 */}
            <button
                type="submit"
                disabled={createMutation.isPending}
            >
                {createMutation.isPending ? '创建中...' : '创建任务'}
            </button>
            {createMutation.isError && (
                <p className="text-red-500">{getErrorMessage(createMutation.error)}</p>
            )}
        </form>
    );
}
```

### 4.1 完成/删除任务

```tsx
function TaskCard({ task }: { task: Task }) {
    const queryClient = useQueryClient();
    
    const completeMutation = useMutation({
        mutationFn: () => taskService.complete(task.id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
    
    const deleteMutation = useMutation({
        mutationFn: () => taskService.delete(task.id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });
    
    return (
        <div>
            <h3>{task.title}</h3>
            <button
                onClick={() => completeMutation.mutate()}
                disabled={completeMutation.isPending}
            >
                完成
            </button>
            <button
                onClick={() => {
                    if (confirm('确定删除？')) deleteMutation.mutate();
                }}
                disabled={deleteMutation.isPending}
            >
                删除
            </button>
        </div>
    );
}
```

---

## 五、乐观更新

先更新 UI，再发请求。请求失败则回滚。

```tsx
const completeMutation = useMutation({
    mutationFn: (taskId: number) => taskService.complete(taskId),
    
    // 乐观更新：请求前先更新缓存
    onMutate: async (taskId) => {
        // 取消正在进行的查询
        await queryClient.cancelQueries({ queryKey: ['tasks'] });
        
        // 保存当前数据（用于回滚）
        const previousTasks = queryClient.getQueryData(['tasks', { status: 'all', page: 1 }]);
        
        // 乐观更新缓存
        queryClient.setQueryData(['tasks', { status: 'all', page: 1 }], (old: any) => ({
            ...old,
            results: old.results.map((t: Task) =>
                t.id === taskId ? { ...t, status: 'completed' } : t
            ),
        }));
        
        return { previousTasks };
    },
    
    // 请求失败，回滚
    onError: (err, taskId, context) => {
        if (context?.previousTasks) {
            queryClient.setQueryData(['tasks', { status: 'all', page: 1 }], context.previousTasks);
        }
    },
    
    // 无论成功失败，都重新获取最新数据
    onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
});
```

---

## 六、自定义 Query Hooks

```typescript
// src/hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taskService } from '@/services/taskService';

export function useTasks(params?: { status?: string; page?: number; search?: string }) {
    return useQuery({
        queryKey: ['tasks', params],
        queryFn: () => taskService.getList(params).then(res => res.data),
    });
}

export function useTask(id: number) {
    return useQuery({
        queryKey: ['tasks', id],
        queryFn: () => taskService.getById(id).then(res => res.data),
        enabled: id > 0,
    });
}

export function useCreateTask() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CreateTaskRequest) => taskService.create(data).then(res => res.data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
    });
}

export function useUpdateTask() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ id, data }: { id: number; data: UpdateTaskRequest }) =>
            taskService.update(id, data).then(res => res.data),
        onSuccess: (_, { id }) => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
            queryClient.invalidateQueries({ queryKey: ['tasks', id] });
        },
    });
}

export function useDeleteTask() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: number) => taskService.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
    });
}

// 使用
function TaskListPage() {
    const { data, isLoading } = useTasks({ status: 'pending', page: 1 });
    const createTask = useCreateTask();
    const deleteTask = useDeleteTask();
    
    return <div>...</div>;
}
```

---

## 七、练习

1. 配置 `QueryClient` 和 `QueryClientProvider`
2. 使用 `useQuery` 获取任务列表，支持过滤和分页
3. 使用 `useMutation` 实现创建、完成、删除任务
4. 实现乐观更新：完成任务时先更新 UI 再发请求
5. 封装自定义 Hook：`useTasks`、`useTask`、`useCreateTask`
6. 安装 React Query DevTools，观察缓存状态
