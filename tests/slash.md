Here's how the corrected section should look:

```dockerfile
 '{ 47
 '( 48 RUN if [ "$BUILD_TYPE" = "development" ]; then \
    49     make runtest -j8 GIT_DESCRIBE=${GIT_DESCRIBE} BUILD_TYPE=${BUILD_TYPE} || true; \
    50 fi
 '. 51
 ') 54 COPY prometheus/config-$BUILD_TYPE.yaml prometheus.template.yaml
 '} 55
```
