from typing import Dict, Any, Callable, Type, TypeVar, Optional
import inspect

T = TypeVar('T')

class DependencyContainer:
    """依赖注入容器，管理所有服务实例"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._singletons: Dict[str, bool] = {}
    
    def register(self, service_type: Type[T], factory: Callable[..., T] = None, 
                singleton: bool = True, key: str = None) -> None:
        """注册服务"""
        # 获取服务名称
        if key is None:
            key = service_type.__name__
        
        # 如果没有提供工厂函数，使用类本身
        if factory is None:
            factory = service_type
        
        self._factories[key] = factory
        self._singletons[key] = singleton
    
    def get(self, service_type: Type[T], key: str = None) -> T:
        """获取服务实例"""
        if key is None:
            key = service_type.__name__
        
        # 检查是否已经实例化过（单例模式）
        if key in self._services and self._singletons.get(key, True):
            return self._services[key]
        
        # 检查是否已注册
        if key not in self._factories:
            raise KeyError(f"服务 '{key}' 未注册")
        
        # 获取工厂函数
        factory = self._factories[key]
        
        # 创建服务实例
        if inspect.isclass(factory):
            # 如果是类，直接实例化
            instance = factory()
        else:
            # 如果是工厂函数，调用它
            instance = factory()
        
        # 如果是单例，保存实例
        if self._singletons.get(key, True):
            self._services[key] = instance
        
        return instance
    
    def inject(self, func: Callable) -> Callable:
        """装饰器：自动注入依赖"""
        signature = inspect.signature(func)
        param_keys = {}
        
        # 遍历函数参数，找出类型标注
        for param_name, param in signature.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
                # 保存参数名和类型
                param_keys[param_name] = param_type
        
        # 创建包装函数
        def wrapper(*args, **kwargs):
            # 复制传入的关键字参数
            new_kwargs = kwargs.copy()
            
            # 为缺少的参数注入依赖
            for param_name, param_type in param_keys.items():
                if param_name not in kwargs:
                    try:
                        # 从容器获取依赖并注入
                        new_kwargs[param_name] = self.get(param_type)
                    except KeyError:
                        # 如果找不到依赖，继续（可能有默认值）
                        pass
            
            # 调用原始函数
            return func(*args, **new_kwargs)
        
        return wrapper
    
    def clear(self) -> None:
        """清除所有服务实例（用于测试）"""
        self._services.clear()

# 创建全局依赖注入容器
container = DependencyContainer()

# 便捷函数：注册服务
def register(service_type: Type[T], factory: Callable[..., T] = None, 
            singleton: bool = True, key: str = None) -> None:
    container.register(service_type, factory, singleton, key)

# 便捷函数：获取服务
def get(service_type: Type[T], key: str = None) -> T:
    return container.get(service_type, key)

# 便捷装饰器：自动注入
def inject(func: Callable) -> Callable:
    return container.inject(func) 